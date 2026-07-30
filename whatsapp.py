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


def _upload_media(file_path):
    """Upload a document to WhatsApp; return its media id."""
    import mimetypes

    mime = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, mime)}
        data = {"messaging_product": "whatsapp", "type": mime}
        r = httpx.post(
            f"{GRAPH}/{os.environ['PHONE_NUMBER_ID']}/media",
            headers={"Authorization": f"Bearer {os.environ['WHATSAPP_TOKEN']}"},
            data=data,
            files=files,
            timeout=60,
        )
    r.raise_for_status()
    return r.json()["id"]


def send_document(to, file_path, filename=None, caption=None):
    """Upload and send a document (resume) to a recipient."""
    media_id = _upload_media(file_path)
    doc = {"id": media_id, "filename": filename or os.path.basename(file_path)}
    if caption:
        doc["caption"] = caption
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "document",
        "document": doc,
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
