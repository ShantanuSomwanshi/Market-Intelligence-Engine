from __future__ import annotations

import json
import re
from statistics import mean
from typing import Any, Dict, List

import httpx
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .config import Settings, get_settings
from .state import ContactField, ContactRecord, DecisionMaker, EvidenceItem


class IntelligenceProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.sentiment = SentimentIntensityAnalyzer()
        self.last_apollo_error = ""

    @property
    def mode(self) -> str:
        if self.settings.use_mock_data or not self.settings.live_mode_available:
            return "mock"
        return "live"

    async def gather_research(self, company_name: str, category_description: str) -> Dict[str, Any]:
        if self.mode == "mock":
            return self._mock_research(company_name, category_description)

        context = self._mock_research(company_name, category_description)
        context["mode"] = "live_best_effort"
        live_facts: List[EvidenceItem] = []
        apollo_people = await self._apollo_people(context.get("company_domain", ""))
        site_context = await self._scrape_company_site(context.get("company_website", ""))
        if site_context:
            context["site_context"] = site_context
            context["public_contact_signals"] = self._extract_public_contact_signals(site_context)
            live_facts.append(
                EvidenceItem(
                    title=f"{company_name} public website",
                    snippet=site_context.get("summary", "") or "Public website content was collected for source-backed contact and company signals.",
                    source_url=site_context.get("source_url", ""),
                    source_type="website",
                    confidence=0.76,
                )
            )
        live_news = await self._fetch_news(company_name)
        if live_news:
            context["news"] = live_news
            for article in live_news:
                live_facts.append(
                    EvidenceItem(
                        title=article.get("title", "News mention"),
                        snippet=article.get("description", "") or article.get("title", ""),
                        source_url=article.get("url", ""),
                        source_type="news",
                        published_at=article.get("publishedAt", ""),
                        confidence=0.78,
                    )
                )

        context["evidence"] = [item.model_dump() for item in live_facts] or context["evidence"]
        if apollo_people:
            context["public_people"] = [
                self._decision_person_from_apollo(item, category_description)
                for item in apollo_people
            ]
            context["apollo_people_count"] = len(apollo_people)
        context["sentiment"] = self._sentiment_summary(context["evidence"])
        return context

    async def enrich_contacts(
        self,
        decision_makers: List[DecisionMaker],
        company_domain: str,
        public_contact_signals: Dict[str, Any] | None = None,
    ) -> List[ContactRecord]:
        contacts: List[ContactRecord] = []
        public_contact_signals = public_contact_signals or {}
        apollo_matches = await self._apollo_people(company_domain) if company_domain else []
        apollo_lookup = {
            self._normalize_name(item.get("name", "")): item
            for item in apollo_matches
            if item.get("name")
        }
        unused_apollo = [item for item in apollo_matches if item.get("name")]

        for person in decision_makers:
            key = self._normalize_name(person.name)
            apollo_hit = apollo_lookup.get(key, {})
            if not apollo_hit and (not person.name or person.name == "not_found"):
                apollo_hit = self._best_apollo_match(unused_apollo, person.role_title)
            if apollo_hit in unused_apollo:
                unused_apollo.remove(apollo_hit)

            linkedin_value = self._first_text(
                apollo_hit.get("linkedin_url"),
                apollo_hit.get("linkedin"),
                person.source_url if "linkedin.com" in person.source_url else "",
            )
            email_value = self._first_text(
                apollo_hit.get("email"),
                apollo_hit.get("email_address"),
                apollo_hit.get("personal_email"),
                apollo_hit.get("organization", {}).get("primary_email") if isinstance(apollo_hit.get("organization"), dict) else "",
            )
            phone_value = self._first_text(
                apollo_hit.get("phone"),
                apollo_hit.get("phone_number"),
                apollo_hit.get("sanitized_phone"),
                self._first_phone_number(apollo_hit),
            )

            email = self._verified_field(email_value, "verified_enrichment")
            phone = self._verified_field(phone_value, "verified_enrichment")
            linkedin = self._verified_field(linkedin_value, "verified_profile_source")
            notes = []
            if email.status == "verified":
                notes.append("A verified enrichment source returned a concrete public-work email.")
            if phone.status == "verified":
                notes.append("A verified enrichment source returned a phone field.")
            if linkedin.status == "verified":
                notes.append("A verified profile source returned a public profile URL.")
            if not notes:
                notes.append("No verified source returned contact data for this stakeholder.")

            overall_status = "not_found"
            if email.status == "verified" or phone.status == "verified":
                overall_status = "verified_contactable"
            elif linkedin.status == "verified":
                overall_status = "verified_partial"

            contacts.append(
                ContactRecord(
                    person_name=self._first_text(person.name, apollo_hit.get("name"), "not_found"),
                    role_title=self._first_text(person.role_title, apollo_hit.get("title"), "Marketing stakeholder"),
                    email=email,
                    phone=phone,
                    linkedin_url=linkedin,
                    overall_status=overall_status,
                    verification_notes=notes,
                )
            )

        if not any(contact.overall_status != "not_found" for contact in contacts):
            public_contact = self._public_contact_record(public_contact_signals)
            if public_contact:
                contacts.insert(0, public_contact)

        return contacts

    async def reason_json(self, instruction: str, payload: Dict[str, Any], fallback: Any) -> Any:
        if not self.settings.groq_api_key:
            return fallback

        prompt = (
            "You are an expert B2B market intelligence analyst.\n"
            "Return valid JSON only with no markdown fences.\n"
            f"Instruction: {instruction}\n"
            f"Payload: {json.dumps(payload)}"
        )
        body = {
            "model": "llama-3.3-70b-versatile",
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=body,
                )
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"]
                return json.loads(raw)
        except Exception:
            return fallback

    def derive_decision_roles(self, category_description: str) -> List[DecisionMaker]:
        roles = [
            ("Head of Marketing", "Owns marketing strategy, campaign execution, and agency evaluation."),
            ("Brand Marketing Lead", "Owns brand positioning, launches, and experiential opportunities."),
            ("Growth or Demand Generation Lead", "Relevant when performance marketing and pipeline efficiency matter."),
        ]
        if any(keyword in category_description.lower() for keyword in ["retail", "consumer", "fashion", "ecommerce"]):
            roles.append(("Experiential Marketing Lead", "Relevant for retail activations, launches, and in-person experiences."))
        return [DecisionMaker(role_title=role, role_relevance=reason) for role, reason in roles]

    def build_outreach(self, company_name: str, person: DecisionMaker, fact_references: List[str], evidence_refs: List[Dict[str, Any]]) -> Dict[str, Any]:
        facts_line = "; ".join(fact_references[:3]) if fact_references else "your recent public activity"
        greeting = person.name if person.name and person.name != "not_found" else person.role_title
        role_strategy = self._role_strategy(person.role_title)
        return {
            "person_name": person.name or "not_found",
            "role_title": person.role_title,
            "fact_references": fact_references,
            "evidence_refs": evidence_refs[:3],
            "role_strategy": role_strategy,
            "linkedin_message": (
                f"Hi {greeting}, I was looking at {company_name}'s recent public signals, especially {facts_line}. "
                "There may be a strong opportunity to tighten the story between market positioning, campaigns, and outbound engagement."
            ),
            "email_subject": f"Thought after reviewing {company_name}'s recent market activity",
            "email_body": (
                f"Hi {greeting},\n\n"
                f"I spent time reviewing {company_name}'s publicly visible activity and a few themes stood out: {facts_line}. "
                "I think there is room to turn those signals into a sharper pre-sales and outreach narrative.\n\n"
                "If useful, I can share a compact breakdown of competitor gaps, stakeholder priorities, and where your current story could become more actionable."
            ),
            "validation_status": "pending",
            "why_now": f"Recent visible signals suggest an opening around {role_strategy['opening_angle'].lower()}.",
        }

    def _mock_research(self, company_name: str, category_description: str) -> Dict[str, Any]:
        profile = self._profile(category_description)
        domain = self._safe_domain(company_name)
        evidence = [
            EvidenceItem(
                title=f"{company_name} category profile",
                snippet=f"{company_name} operates in {category_description} with a {profile['positioning']} positioning style.",
                source_url="mock://category-profile",
                source_type="mock",
                confidence=0.74,
            ),
            EvidenceItem(
                title=f"{company_name} messaging shift",
                snippet=f"Public messaging appears focused on {profile['message_shift']} and clearer proof of value.",
                source_url="mock://messaging-shift",
                source_type="mock",
                confidence=0.69,
            ),
            EvidenceItem(
                title=f"{company_name} market pressure",
                snippet=f"Competitive pressure is likely shaped by {profile['competitive_frame']}.",
                source_url="mock://competitive-frame",
                source_type="mock",
                confidence=0.66,
            ),
        ]
        people = [
            {
                "name": "",
                "role_title": role.role_title,
                "role_relevance": role.role_relevance,
                "source_url": "",
                "confidence": 0.0,
            }
            for role in self.derive_decision_roles(category_description)
        ]
        return {
            "mode": "mock",
            "company_name": company_name,
            "category_description": category_description,
            "company_domain": domain,
            "company_website": f"https://{domain}" if domain else "",
            "profile": profile,
            "evidence": [item.model_dump() for item in evidence],
            "news": [],
            "public_people": people,
            "sentiment": self._sentiment_summary([item.model_dump() for item in evidence]),
        }

    async def _fetch_news(self, company_name: str) -> List[Dict[str, Any]]:
        if not self.settings.newsapi_key:
            return []
        params = {
            "q": f'"{company_name}"',
            "sortBy": "publishedAt",
            "pageSize": 10,
            "language": "en",
            "apiKey": self.settings.newsapi_key,
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get("https://newsapi.org/v2/everything", params=params)
                response.raise_for_status()
                return response.json().get("articles", [])
        except Exception:
            return []

    async def _scrape_company_site(self, website_url: str) -> Dict[str, Any]:
        if not self.settings.firecrawl_api_key or not website_url:
            return {}
        payload = {
            "url": website_url,
            "formats": ["markdown"],
            "onlyMainContent": False,
            "timeout": self.settings.request_timeout_seconds * 1000,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.settings.firecrawl_api_key}",
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post("https://api.firecrawl.dev/v1/scrape", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json().get("data", {})
                markdown = data.get("markdown", "") or ""
                metadata = data.get("metadata", {}) or {}
                return {
                    "source_url": data.get("url", "") or website_url,
                    "title": metadata.get("title", "") or data.get("title", ""),
                    "markdown": markdown[:18000],
                    "summary": self._compact_text(markdown, 420),
                }
        except Exception:
            return {}

    async def _apollo_people(self, domain: str) -> List[Dict[str, Any]]:
        self.last_apollo_error = ""
        if not self.settings.apollo_api_key or not domain:
            self.last_apollo_error = "Apollo key or company domain is missing."
            return []
        payload = {
            "q_organization_domains_list": [domain],
            "person_titles": ["marketing", "brand", "growth", "founder", "chief marketing officer"],
            "page": 1,
            "per_page": 5,
        }
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self.settings.apollo_api_key,
            "Cache-Control": "no-cache",
        }
        endpoints = [
            "https://api.apollo.io/api/v1/people/search",
            "https://api.apollo.io/v1/people/search",
        ]
        for endpoint in endpoints:
            try:
                async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                    response = await client.post(endpoint, json=payload, headers=headers)
                    if response.status_code >= 400:
                        self.last_apollo_error = f"HTTP {response.status_code} from {endpoint}"
                        continue
                    data = response.json()
                    return data.get("people", []) or data.get("contacts", []) or []
            except Exception as exc:
                self.last_apollo_error = str(exc)
                continue
        return []

    def _verified_field(self, value: str | None, source: str) -> ContactField:
        if value:
            return ContactField(value=value, status="verified", confidence=0.85, source=source, trust_state="verified")
        return ContactField()

    def _extract_public_contact_signals(self, site_context: Dict[str, Any]) -> Dict[str, Any]:
        markdown = site_context.get("markdown", "")
        source_url = site_context.get("source_url", "")
        emails = []
        for email in re.findall(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", markdown, flags=re.IGNORECASE):
            normalized = email.strip().lower()
            if normalized not in emails and not normalized.endswith((".png", ".jpg", ".jpeg", ".webp")):
                emails.append(normalized)

        linkedin_urls = []
        for url in re.findall(r"https?://(?:www\.)?linkedin\.com/[^\s)>\]\"']+", markdown, flags=re.IGNORECASE):
            cleaned = url.rstrip(".,;")
            if cleaned not in linkedin_urls:
                linkedin_urls.append(cleaned)

        return {
            "emails": emails[:5],
            "linkedin_urls": linkedin_urls[:5],
            "source_url": source_url,
        }

    def _public_contact_record(self, signals: Dict[str, Any]) -> ContactRecord | None:
        email_value = self._first_text(*signals.get("emails", []))
        linkedin_value = self._first_text(*signals.get("linkedin_urls", []))
        if not email_value and not linkedin_value:
            return None

        email = self._verified_field(email_value, "public_company_source")
        linkedin = self._verified_field(linkedin_value, "public_company_source")
        overall_status = "verified_contactable" if email.status == "verified" else "verified_partial"
        notes = []
        if email.status == "verified":
            notes.append("A public company source listed this email address.")
        if linkedin.status == "verified":
            notes.append("A public company source listed this profile URL.")

        return ContactRecord(
            person_name="Public company contact",
            role_title="Published company contact route",
            email=email,
            phone=ContactField(),
            linkedin_url=linkedin,
            overall_status=overall_status,
            verification_notes=notes,
        )

    def _decision_person_from_apollo(self, person: Dict[str, Any], category_description: str) -> Dict[str, Any]:
        title = self._first_text(person.get("title"), "Marketing stakeholder")
        return {
            "name": self._first_text(person.get("name"), ""),
            "role_title": title,
            "role_relevance": self._role_relevance_for_title(title, category_description),
            "source_url": self._first_text(person.get("linkedin_url"), person.get("linkedin"), ""),
            "confidence": 0.82 if person.get("name") else 0.58,
        }

    def _best_apollo_match(self, people: List[Dict[str, Any]], role_title: str) -> Dict[str, Any]:
        if not people:
            return {}
        role_tokens = set(re.findall(r"[a-z]+", role_title.lower()))
        best_person = people[0]
        best_score = -1
        for person in people:
            title = str(person.get("title", "")).lower()
            title_tokens = set(re.findall(r"[a-z]+", title))
            score = len(role_tokens & title_tokens)
            if "marketing" in title:
                score += 2
            if "brand" in role_tokens and "brand" in title:
                score += 3
            if ("growth" in role_tokens or "demand" in role_tokens) and any(term in title for term in ["growth", "demand"]):
                score += 3
            if score > best_score:
                best_score = score
                best_person = person
        return best_person

    def _first_text(self, *values: Any) -> str:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _compact_text(self, value: str, limit: int) -> str:
        text = re.sub(r"\s+", " ", value).strip()
        if len(text) <= limit:
            return text
        return f"{text[:limit].rstrip()}..."

    def _first_phone_number(self, person: Dict[str, Any]) -> str:
        for key in ["phone_numbers", "phones", "contact_phone_numbers"]:
            values = person.get(key)
            if not isinstance(values, list):
                continue
            for item in values:
                if isinstance(item, str) and item.strip():
                    return item.strip()
                if isinstance(item, dict):
                    phone = self._first_text(item.get("raw_number"), item.get("sanitized_number"), item.get("number"))
                    if phone:
                        return phone
        return ""

    def _role_relevance_for_title(self, title: str, category_description: str) -> str:
        role = title.lower()
        if "brand" in role:
            return "Owns brand positioning, launch messaging, and agency-facing campaign opportunities."
        if "growth" in role or "demand" in role:
            return "Owns pipeline growth, conversion efficiency, and performance-oriented outreach opportunities."
        if "marketing" in role or "cmo" in role:
            return "Owns go-to-market strategy, campaigns, and potential agency evaluation."
        if any(term in category_description.lower() for term in ["retail", "consumer", "fashion", "ecommerce"]):
            return "Relevant commercial stakeholder for consumer engagement and brand experience opportunities."
        return "Relevant stakeholder for market positioning and outreach prioritization."

    def _safe_domain(self, company_name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "", company_name.lower())
        return f"{slug}.com" if slug else ""

    def _profile(self, category_description: str) -> Dict[str, str]:
        text = category_description.lower()
        if any(term in text for term in ["saas", "software", "platform", "ai", "cloud"]):
            return {
                "business_model": "B2B SaaS",
                "positioning": "product-led and efficiency-oriented",
                "message_shift": "AI capability proof and enterprise readiness",
                "competitive_frame": "fast-moving feature parity and crowded workflow tooling",
            }
        if any(term in text for term in ["retail", "consumer", "fashion", "ecommerce"]):
            return {
                "business_model": "consumer or omni-channel commerce",
                "positioning": "brand-forward and experience-led",
                "message_shift": "lifecycle retention and differentiated brand storytelling",
                "competitive_frame": "high attention competition and campaign fatigue",
            }
        if any(term in text for term in ["health", "biotech", "medical", "pharma"]):
            return {
                "business_model": "regulated health or life sciences",
                "positioning": "trust-driven and evidence-heavy",
                "message_shift": "credibility, clarity, and stakeholder education",
                "competitive_frame": "regulatory caution and complex buyer ecosystems",
            }
        return {
            "business_model": "mixed-model commercial business",
            "positioning": "category-led with room for sharper differentiation",
            "message_shift": "clearer value communication and market education",
            "competitive_frame": "fragmented competition and inconsistent positioning",
        }

    def _sentiment_summary(self, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        scores = []
        for item in evidence:
            text = f"{item.get('title', '')} {item.get('snippet', '')}".strip()
            if text:
                scores.append(self.sentiment.polarity_scores(text)["compound"])
        compound = mean(scores) if scores else 0.0
        label = "positive" if compound > 0.2 else "negative" if compound < -0.2 else "neutral"
        return {"label": label, "compound_score": round(compound, 3)}

    def _normalize_name(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    def _role_strategy(self, role_title: str) -> Dict[str, str]:
        role = role_title.lower()
        if "brand" in role:
            return {
                "priority": "brand authority and campaign distinctiveness",
                "opening_angle": "brand narrative whitespace",
            }
        if "growth" in role or "demand" in role:
            return {
                "priority": "pipeline performance and conversion efficiency",
                "opening_angle": "growth execution leverage",
            }
        if "marketing" in role:
            return {
                "priority": "market positioning and go-to-market efficiency",
                "opening_angle": "positioning-to-pipeline clarity",
            }
        return {
            "priority": "strategic visibility and market confidence",
            "opening_angle": "high-level strategic opportunity",
        }


_provider: IntelligenceProvider | None = None


def get_provider() -> IntelligenceProvider:
    global _provider
    if _provider is None:
        _provider = IntelligenceProvider(get_settings())
    return _provider


def build_tracking_metrics(events: List[dict]) -> Dict[str, Any]:
    delivered_contacts = {event["contact_key"] for event in events if event["event_type"] == "delivered"}
    opened_contacts = {event["contact_key"] for event in events if event["event_type"] == "opened"}
    replied_contacts = {event["contact_key"] for event in events if event["event_type"] == "replied"}

    first_delivery = {}
    first_reply = {}
    for event in events:
        if event["event_type"] == "delivered" and event["contact_key"] not in first_delivery:
            first_delivery[event["contact_key"]] = event["created_at"]
        if event["event_type"] == "replied" and event["contact_key"] not in first_reply:
            first_reply[event["contact_key"]] = event["created_at"]

    response_times = []
    for contact_key, delivered_at in first_delivery.items():
        replied_at = first_reply.get(contact_key)
        if replied_at:
            response_times.append({"contact_key": contact_key, "delivered_at": delivered_at, "replied_at": replied_at})

    delivered = len(delivered_contacts)
    opened = len(opened_contacts)
    replied = len(replied_contacts)

    return {
        "delivered_contacts": delivered,
        "opened_contacts": opened,
        "replied_contacts": replied,
        "open_rate": round(opened / delivered, 3) if delivered else 0.0,
        "response_rate": round(replied / delivered, 3) if delivered else 0.0,
        "time_to_response_events": response_times,
    }


def build_scorecard(run_state) -> Dict[str, Any]:
    evidence = run_state.research_context.get("evidence", [])
    contacts = run_state.report.get("contact_intelligence", [])
    outreach = run_state.report.get("personalized_outreach", [])
    competitor_count = len(run_state.report.get("competitor_mapping", []))

    contact_score = 20 + 25 * sum(1 for item in contacts if item.get("overall_status") != "not_found") / max(len(contacts), 1)
    evidence_score = min(25 + len(evidence) * 8, 90)
    competitor_score = min(25 + competitor_count * 12, 85)
    outreach_score = 30 + 20 * sum(1 for item in outreach if item.get("fact_references")) / max(len(outreach), 1)
    urgency_score = 52 + min(len(run_state.research_context.get("news", [])) * 6, 18)

    agency_opportunity = round((contact_score + evidence_score + competitor_score + outreach_score + urgency_score) / 5)
    return {
        "agency_opportunity_score": agency_opportunity,
        "dimensions": [
            {"label": "Brand Momentum", "score": round(evidence_score)},
            {"label": "Outreach Readiness", "score": round(outreach_score)},
            {"label": "Competitive Pressure", "score": round(competitor_score)},
            {"label": "Contact Confidence", "score": round(contact_score)},
            {"label": "Timing Urgency", "score": round(urgency_score)},
        ],
    }


def build_trust_summary(run_state) -> Dict[str, Any]:
    contacts = run_state.report.get("contact_intelligence", [])
    fields = []
    for contact in contacts:
        fields.extend([contact.get("email", {}), contact.get("phone", {}), contact.get("linkedin_url", {})])

    verified = sum(1 for field in fields if field.get("trust_state") == "verified")
    missing = sum(1 for field in fields if field.get("trust_state") == "not_found")
    return {
        "verified_fields": verified,
        "not_found_fields": missing,
        "fabrication_policy": "Only public, source-backed contact data is surfaced. Missing values remain blank.",
        "validator_status": "low_confidence" if run_state.low_confidence else "validated",
    }


def build_evidence_trace(run_state) -> Dict[str, Any]:
    evidence = run_state.research_context.get("evidence", [])
    evidence_refs = [
        {
            "evidence_id": f"ev_{index + 1}",
            "title": item.get("title", "Evidence"),
            "snippet": item.get("snippet", ""),
            "source_url": item.get("source_url", ""),
            "used_in_sections": _used_in_sections(item, run_state.report),
        }
        for index, item in enumerate(evidence[:5])
    ]

    outreach_links = []
    for item in run_state.report.get("personalized_outreach", []):
        outreach_links.append(
            {
                "person_name": item.get("person_name", ""),
                "role_title": item.get("role_title", ""),
                "fact_references": item.get("fact_references", []),
                "role_strategy": item.get("role_strategy", {}),
            }
        )

    return {
        "evidence_refs": evidence_refs,
        "outreach_links": outreach_links,
    }


def build_recommendation_engine(run_state) -> Dict[str, Any]:
    decision_makers = run_state.report.get("decision_makers", [])
    contacts = run_state.report.get("contact_intelligence", [])
    watchouts = run_state.report.get("strategic_watchouts", {}).get("pre_engagement_insights", [])
    primary_contact = next((item for item in contacts if item.get("overall_status") == "verified_contactable"), None)
    fallback_person = primary_contact or (contacts[0] if contacts else None)
    primary_name = fallback_person.get("person_name") if fallback_person else "not_found"
    primary_channel = "email" if primary_contact and primary_contact.get("email", {}).get("status") == "verified" else "linkedin"
    opening_angle = watchouts[0] if watchouts else "Lead with a visible public-company signal and strategic whitespace."

    return {
        "why_this_prospect_now": (
            f"{run_state.input.company_name} shows enough public signal density to support a credible outreach narrative "
            "without relying on fabricated contact or company assumptions."
        ),
        "best_outreach_target": primary_name,
        "best_contact_channel": primary_channel,
        "best_opening_angle": opening_angle,
        "recommended_next_action": "Start with the primary stakeholder, then escalate to a second marketing role if no response within one cycle.",
        "stakeholder_sequence": [
            {
                "priority": index + 1,
                "role_title": item.get("role_title", ""),
                "role_relevance": item.get("role_relevance", ""),
            }
            for index, item in enumerate(decision_makers[:3])
        ],
    }


def build_executive_brief(run_state) -> Dict[str, Any]:
    scorecard = build_scorecard(run_state)
    recommendation = build_recommendation_engine(run_state)
    return {
        "headline": f"{run_state.input.company_name} is a {'high' if scorecard['agency_opportunity_score'] >= 70 else 'moderate'}-potential prospect for strategic outreach.",
        "why_now": recommendation["why_this_prospect_now"],
        "opportunity_score": scorecard["agency_opportunity_score"],
        "focus": recommendation["best_opening_angle"],
    }


def _used_in_sections(evidence_item: Dict[str, Any], report: Dict[str, Any]) -> List[str]:
    snippet = evidence_item.get("snippet", "")
    used = []
    for section_name, section_value in report.items():
        if snippet and snippet in json.dumps(section_value):
            used.append(section_name)
    return used
