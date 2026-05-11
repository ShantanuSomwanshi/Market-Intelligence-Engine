from ..state import RunState, set_report_section


EVENT_KEYWORDS = [
    "event",
    "conference",
    "summit",
    "webinar",
    "expo",
    "exhibition",
    "booth",
    "roadshow",
    "activation",
    "launch",
    "showcase",
    "keynote",
]


def _event_type(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ["webinar", "virtual", "online"]):
        return "virtual"
    if any(term in lowered for term in ["expo", "exhibition", "booth", "trade show"]):
        return "exhibition"
    if any(term in lowered for term in ["launch", "showcase", "keynote"]):
        return "launch_or_showcase"
    if any(term in lowered for term in ["roadshow", "activation", "experience"]):
        return "brand_activation"
    return "public_event_signal"


def _event_signals(evidence: list[dict]) -> list[dict]:
    events = []
    for item in evidence:
        text = f"{item.get('title', '')} {item.get('snippet', '')}"
        if not any(keyword in text.lower() for keyword in EVENT_KEYWORDS):
            continue
        events.append(
            {
                "name": item.get("title", "Public event signal"),
                "format": _event_type(text),
                "scale": "publicly visible",
                "date": item.get("published_at", ""),
                "outcomes": item.get("snippet", ""),
                "source_url": item.get("source_url", ""),
            }
        )
    return events[:5]


async def run(state: RunState) -> RunState:
    evidence = state.research_context.get("evidence", [])
    events = _event_signals(evidence)
    category = state.input.category_description.lower()

    if events:
        summary = "Public event, launch, or activation signals were found in the available source bundle."
    elif any(term in category for term in ["event", "exhibition", "booth", "activation", "roadshow", "experiential"]):
        summary = (
            "The category itself is event-led, but no named public event record was confidently extracted from the current source bundle. "
            "Use this as a prompt for manual portfolio or case-study review before outreach."
        )
    else:
        summary = (
            "No named public event record was confidently extracted from the current source bundle. "
            "Treat events as a secondary watchlist area rather than a primary outreach hook."
        )

    set_report_section(
        state,
        "events_footprint",
        {
            "events": events,
            "summary": summary,
        },
    )
    return state
