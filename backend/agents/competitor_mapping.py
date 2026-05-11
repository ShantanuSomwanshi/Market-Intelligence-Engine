from ..state import RunState, set_report_section


COMPANY_COMPETITORS = {
    "hubspot": [
        ("Salesforce", "Enterprise CRM and marketing cloud", "Very strong enterprise depth and ecosystem", "Can feel heavier and more complex for mid-market teams", "Salesforce is the enterprise benchmark; HubSpot is stronger for simpler inbound-led adoption."),
        ("Zoho CRM", "SMB and mid-market CRM suite", "Broad suite with aggressive pricing", "Less premium brand perception in enterprise marketing teams", "Zoho competes on breadth and value; HubSpot competes on usability and marketing-led growth."),
        ("ActiveCampaign", "Marketing automation and customer experience", "Strong automation and lifecycle marketing", "Less complete as an all-in-one CRM platform", "ActiveCampaign pressures HubSpot in automation-heavy use cases."),
        ("Mailchimp", "Email marketing and audience engagement", "High awareness among small businesses", "Weaker CRM and sales platform depth", "Mailchimp overlaps with HubSpot at the entry marketing layer."),
        ("Adobe Marketo Engage", "Enterprise marketing automation", "Strong enterprise campaign orchestration", "Less approachable for smaller teams", "Marketo competes in larger marketing operations environments."),
    ],
    "salesforce": [
        ("HubSpot", "CRM and marketing automation", "Fast adoption and strong SMB/mid-market appeal", "Less enterprise complexity than Salesforce", "HubSpot is the simpler growth platform alternative."),
        ("Microsoft Dynamics 365", "Enterprise CRM and business applications", "Strong Microsoft ecosystem integration", "Can be implementation-heavy", "Dynamics competes where Microsoft stack alignment matters."),
        ("Zoho CRM", "Value-led CRM suite", "Affordable broad suite", "Less enterprise perception than Salesforce", "Zoho pressures price-sensitive CRM decisions."),
        ("Oracle CX", "Enterprise customer experience suite", "Deep enterprise data and CX footprint", "Complex adoption and lower product-led appeal", "Oracle competes in large enterprise transformation deals."),
    ],
    "shopify": [
        ("WooCommerce", "Open-source ecommerce for WordPress", "Huge ecosystem and ownership flexibility", "Requires more setup and maintenance", "WooCommerce competes when merchants want control and WordPress alignment."),
        ("BigCommerce", "Hosted ecommerce platform", "Strong mid-market and B2B commerce features", "Smaller app and brand ecosystem than Shopify", "BigCommerce is a direct hosted-commerce alternative."),
        ("Wix", "Website builder with commerce", "Simple site creation for small businesses", "Less commerce depth for scaling merchants", "Wix competes at the small-business entry point."),
        ("Squarespace", "Design-led website and commerce builder", "Strong templates and creator appeal", "Less advanced commerce operations", "Squarespace competes for brand-led small merchants."),
    ],
    "apple": [
        ("Samsung", "Consumer electronics and smartphones", "Broad hardware portfolio and global scale", "Less control over full OS/service ecosystem", "Samsung is Apple's closest premium device competitor."),
        ("Google", "Android, AI, services, and Pixel devices", "Strong AI and software ecosystem", "Hardware pull is narrower than Apple's", "Google competes through Android, services, and AI integration."),
        ("Microsoft", "Personal computing, cloud, and productivity", "Enterprise software and productivity strength", "Less consumer hardware lifestyle pull", "Microsoft overlaps in devices, productivity, and ecosystem lock-in."),
        ("Sony", "Consumer electronics and entertainment", "Strong entertainment and premium device heritage", "Less integrated mobile/computing ecosystem", "Sony competes in entertainment-led hardware categories."),
    ],
    "google": [
        ("Microsoft", "Search, cloud, productivity, and AI", "Enterprise distribution and OpenAI partnership", "Consumer search default is weaker than Google", "Microsoft is Google's strongest cross-category AI/cloud/search challenger."),
        ("Meta", "Digital advertising and social platforms", "Massive social ad inventory", "Weaker search intent data", "Meta competes for advertising budgets and AI attention."),
        ("Amazon", "Cloud, ads, ecommerce, and AI infrastructure", "AWS scale and commerce intent data", "Less dominant in open web search", "Amazon competes in cloud and retail media advertising."),
        ("Apple", "Consumer ecosystem and privacy-led services", "Premium device ecosystem control", "Less advertising/search breadth", "Apple competes through platform control and privacy positioning."),
    ],
    "notion": [
        ("Coda", "Docs, tables, and workflow apps", "Flexible doc-app building model", "Smaller mainstream awareness", "Coda is a direct workspace-building alternative."),
        ("Confluence", "Team documentation and knowledge base", "Enterprise adoption through Atlassian", "Less modern all-in-one workspace feel", "Confluence competes in enterprise knowledge management."),
        ("Asana", "Work management and collaboration", "Strong project management structure", "Less flexible for docs and wikis", "Asana competes when teams prioritize structured execution."),
        ("ClickUp", "All-in-one work management", "Broad feature set across tasks/docs/goals", "Can feel crowded for simple knowledge workflows", "ClickUp pressures Notion through feature breadth."),
    ],
    "nike": [
        ("Adidas", "Global sportswear and lifestyle brand", "Strong sports heritage and fashion collaborations", "Brand momentum can vary by market", "Adidas is Nike's most direct global competitor."),
        ("Puma", "Sportswear and lifestyle footwear", "Strong lifestyle and football presence", "Smaller scale than Nike", "Puma competes through culture-led sportswear moments."),
        ("Under Armour", "Performance athletic apparel", "Performance credibility in training categories", "Lower lifestyle pull than Nike", "Under Armour competes in performance-first segments."),
        ("Lululemon", "Premium activewear and community retail", "Strong community and premium apparel positioning", "Less broad footwear/sport portfolio", "Lululemon pressures Nike in premium active lifestyle."),
    ],
    "steponexp": [
        ("George P. Johnson", "Experience marketing and brand activations", "Large global experiential footprint", "May be less accessible for regional activations", "A global benchmark for enterprise experience marketing."),
        ("Jack Morton", "Brand experience agency", "Strong creative experiential reputation", "Premium agency positioning can be costly", "A direct reference point for strategic brand experiences."),
        ("Freeman", "Events, exhibits, and trade show services", "Deep exhibition and event operations scale", "May be more operations-led than boutique creative", "A major competitor for exhibition and event execution."),
        ("Pico Group", "Brand activation and exhibition services", "Strong Asia-Pacific events footprint", "Less locally specialized in some markets", "Competes where scale and regional execution matter."),
    ],
}


CATEGORY_COMPETITORS = [
    (
        ["crm", "marketing automation", "customer relationship", "inbound marketing"],
        COMPANY_COMPETITORS["hubspot"],
    ),
    (
        ["ecommerce", "commerce", "merchant", "online store"],
        COMPANY_COMPETITORS["shopify"],
    ),
    (
        ["event", "exhibition", "booth", "activation", "roadshow", "experiential"],
        COMPANY_COMPETITORS["steponexp"],
    ),
    (
        ["productivity", "workspace", "wiki", "docs", "collaboration"],
        COMPANY_COMPETITORS["notion"],
    ),
    (
        ["retail", "consumer", "fashion", "sportswear"],
        COMPANY_COMPETITORS["nike"],
    ),
    (
        ["search", "advertising", "cloud", "ai", "internet services"],
        COMPANY_COMPETITORS["google"],
    ),
    (
        ["consumer technology", "devices", "smartphone", "software and services"],
        COMPANY_COMPETITORS["apple"],
    ),
    (
        ["health", "biotech", "medical", "pharma"],
        [
            ("Pfizer", "Global pharmaceutical company", "Scale, distribution, and clinical portfolio", "Less focused on mRNA-first innovation", "A global pharma benchmark for regulated healthcare communication."),
            ("BioNTech", "mRNA therapeutics and vaccines", "Strong mRNA science credibility", "Narrower commercial footprint", "A direct scientific competitor in mRNA narratives."),
            ("Novavax", "Vaccine biotechnology", "Protein-based vaccine differentiation", "Smaller scale and lower brand awareness", "A challenger in vaccine-focused biotech."),
            ("GSK", "Global vaccines and pharma", "Established vaccine portfolio", "Less associated with breakthrough mRNA positioning", "Competes through trust, scale, and healthcare relationships."),
        ],
    ),
]


def _company_key(company_name: str) -> str:
    return "".join(ch for ch in company_name.lower() if ch.isalnum())


def _pick_competitors(company_name: str, category: str) -> list[tuple[str, str, str, str, str]]:
    company_key = _company_key(company_name)
    if company_key in COMPANY_COMPETITORS:
        return COMPANY_COMPETITORS[company_key]

    text = f"{company_name} {category}".lower()
    for keywords, competitors in CATEGORY_COMPETITORS:
        if any(keyword in text for keyword in keywords):
            return competitors

    return [
        ("Category Leader", "Largest visible player in the category", "Scale and awareness", "May move slower than focused challengers", "Benchmark competitor based on category leadership."),
        ("Specialist Challenger", "Focused category specialist", "Sharper niche positioning", "Lower scale and distribution", "Competes through specialization and speed."),
        ("Platform Alternative", "Broader platform with overlapping use cases", "Suite breadth and ecosystem", "Can be less focused on the target use case", "Competes when buyers prefer consolidated platforms."),
        ("Low-Cost Alternative", "Value-led competitor", "Pricing and accessibility", "May lack premium positioning or advanced capabilities", "Competes for budget-sensitive buyers."),
    ]


def _competitors(company_name: str, category: str) -> list[dict]:
    competitors = _pick_competitors(company_name, category)
    return [
        {
            "competitor_name": name,
            "category_fit": category_fit,
            "brand_activity": [
                "Relevant public competitor for positioning, campaign comparison, and outreach framing.",
                "Use recent launches/news as live evidence when available.",
            ],
            "strengths": [strength],
            "gaps_vs_target": [gap],
            "relative_position": relative_position,
        }
        for name, category_fit, strength, gap, relative_position in competitors[:5]
        if _company_key(name) != _company_key(company_name)
    ][:4]


async def run(state: RunState) -> RunState:
    set_report_section(
        state,
        "competitor_mapping",
        _competitors(state.input.company_name, state.input.category_description),
    )
    return state
