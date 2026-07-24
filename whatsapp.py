"""Send messages via the Meta WhatsApp Cloud API."""
import os

import httpx

GRAPH = "https://graph.facebook.com/v21.0"


def _url():
    return f"{GRAPH}/{os.environ['PHONE_NUMBER_ID']}/messages"


def _headers():
    return {
        "Authorization": f"Bearer {os.environ['WHATSAPP_TOKEN']}",
        "Content-Type": "application/json",
    }


def send_text(to, body):
    """Send a free-form text message (only valid inside the 24h customer window)."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }
    r = httpx.post(_url(), headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def send_template(to, template_name, lang="en_US", components=None):
    """Send a pre-approved template (use outside the 24h window / for outreach)."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": lang},
        },
    }
    if components:
        payload["template"]["components"] = components
    r = httpx.post(_url(), headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()
