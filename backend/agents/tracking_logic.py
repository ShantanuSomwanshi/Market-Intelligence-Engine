from ..state import RunState, set_report_section


async def run(state: RunState) -> RunState:
    set_report_section(
        state,
        "outreach_tracking_logic",
        {
            "tracking_pixel_demo": {
                "mechanism": "A unique 1x1 pixel endpoint is generated per run and contact.",
                "example_pixel_url": f"/track/open/{state.run_id}/contact-key/pixel.png",
            },
            "imap_response_tracking": {
                "mechanism": "Demo webhook/IMAP handler records replies against a run and contact key.",
                "matching_key": "reply_to_message_id_or_contact_key",
            },
            "metrics": {
                "open_rate_formula": "opened_contacts / delivered_contacts",
                "response_rate_formula": "replied_contacts / delivered_contacts",
                "time_to_response_formula": "first_reply_timestamp - sent_timestamp",
            },
        },
    )
    return state
