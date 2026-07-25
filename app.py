"""FastAPI webhook for the WhatsApp bench-sales agent.

Run:  uvicorn app:app --reload --port 8000
Then expose with ngrok:  ngrok http 8000
Configure the ngrok HTTPS URL + /webhook in Meta App > WhatsApp > Configuration.
"""
import hashlib
import hmac
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response

load_dotenv()

import store
import whatsapp
from brain import generate

store.init()
app = FastAPI(title="Bench Sales WhatsApp Agent")

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
APP_SECRET = os.environ.get("APP_SECRET", "")
ALLOWED = {s.strip().lstrip("+") for s in os.environ.get("ALLOWED_SENDERS", "").split(",") if s.strip()}


@app.get("/webhook")
async def verify(request: Request):
    """Meta calls this once to verify the webhook."""
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge", ""), media_type="text/plain")
    return Response(status_code=403)


def _valid_signature(body: bytes, sig_header: str) -> bool:
    if not APP_SECRET:
        return True  # signature check disabled
    if not sig_header or not sig_header.startswith("sha256="):
        return False
    expected = hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_header.split("=", 1)[1])


@app.post("/webhook")
async def incoming(request: Request):
    raw = await request.body()
    if not _valid_signature(raw, request.headers.get("X-Hub-Signature-256", "")):
        return Response(status_code=403)

    data = await request.json()
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                if msg.get("type") != "text":
                    continue
                _handle(msg["from"], msg["text"]["body"])
    return {"status": "ok"}


def _handle(wa_id: str, text: str):
    if ALLOWED and wa_id.lstrip("+") not in ALLOWED:
        return  # ignore senders not on the allow-list

    store.add_message(wa_id, "vendor", text)
    hist = store.history(wa_id)
    result = generate(hist[:-1], text)  # hist already includes this msg; pass prior

    reply, topic, decision = result["reply"], result["topic"], result["decision"]

    if decision == "auto":
        try:
            whatsapp.send_text(wa_id, reply)
            store.add_message(wa_id, "agent", reply)
            print(f"[AUTO->{wa_id}] ({topic}) {reply}")
        except Exception as e:
            # Common in dev mode: recipient not in allowed list. Keep the reply as
            # a draft instead of crashing the request, so nothing is lost.
            detail = getattr(getattr(e, "response", None), "text", str(e))
            draft_id = store.add_draft(wa_id, reply, topic)
            print(f"[SEND FAILED -> saved as DRAFT #{draft_id} for {wa_id}] {detail}")
    else:
        draft_id = store.add_draft(wa_id, reply, topic)
        print(f"[DRAFT #{draft_id} for {wa_id}] ({topic}, conf={result.get('confidence')}) {reply}")


@app.get("/health")
async def health():
    return {"ok": True, "pending_drafts": len(store.pending_drafts())}


@app.get("/messages")
async def messages(key: str = "", wa_id: str = ""):
    """View stored conversations. Protected by ?key=<VERIFY_TOKEN>.
    Open https://<your-app>/messages?key=<VERIFY_TOKEN> in a browser.
    """
    if key != VERIFY_TOKEN or not VERIFY_TOKEN:
        return Response(status_code=403, content="Forbidden — add ?key=<VERIFY_TOKEN>")
    rows = store.history(wa_id.lstrip("+")) if wa_id else store.recent_messages()
    html = [
        "<html><head><meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<style>body{font-family:Arial;max-width:700px;margin:20px auto;padding:0 12px}",
        ".vendor{background:#eee;padding:8px 12px;border-radius:10px;margin:6px 0}",
        ".agent{background:#d9fdd3;padding:8px 12px;border-radius:10px;margin:6px 0;text-align:right}",
        ".num{color:#888;font-size:12px}</style></head><body>",
        f"<h3>Conversations ({len(rows)} messages)</h3>",
    ]
    for r in rows:
        cls = "agent" if r["role"] == "agent" else "vendor"
        who = "" if wa_id else f"<div class='num'>{r.get('wa_id','')}</div>"
        html.append(f"{who}<div class='{cls}'>{r['body']}</div>")
    html.append("</body></html>")
    return Response(content="\n".join(html), media_type="text/html")
