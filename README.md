# WhatsApp Bench-Sales Agent

Official **WhatsApp Business Cloud API** agent that replies to IT staffing vendors.
It reads bundled consultant profiles from `consultants/*.json`, drafts replies with Claude
(Sonnet 5), and either **auto-sends** simple factual replies or **queues a draft** for
your approval (mixed autonomy).

```
Vendor -> Meta Cloud API -> /webhook (FastAPI) -> Claude -> auto-send OR draft
                                                              (review.py to approve)
```

## Files
| File | Purpose |
|---|---|
| `app.py` | FastAPI webhook (receives vendor messages, sends auto-replies) |
| `brain.py` | Builds the prompt, calls Claude, decides auto vs draft |
| `whatsapp.py` | Send text / template via Cloud API |
| `consultants.py` | Loads consultant profiles from consultants/*.json |
| `store.py` | SQLite: conversation history + pending drafts |
| `review.py` | CLI to approve/edit/reject queued drafts |
| `config/rules.json` | Tone, auto-send topics, never-share list |

## One-time Meta setup
1. Go to **developers.facebook.com** → create an App → add the **WhatsApp** product.
2. In **WhatsApp → API Setup**: note the **Phone number ID** and generate a token
   (create a **System User** for a permanent token — the default one expires in 24h).
3. Get your **App Secret** from **App Settings → Basic** (for signature verification).

## Local run (testing)
```bash
cd whatsapp_agent
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env                                # then fill in values
uvicorn app:app --reload --port 8000
```
In another terminal, expose it over HTTPS (Meta requires HTTPS):
```bash
ngrok http 8000
```
Copy the `https://xxxx.ngrok-free.app` URL. In **Meta App → WhatsApp → Configuration**:
- **Callback URL:** `https://xxxx.ngrok-free.app/webhook`
- **Verify token:** the same `VERIFY_TOKEN` you put in `.env`
- Click **Verify and save**, then **Subscribe** to the `messages` field.

## Test it
Message your WhatsApp test number from your personal phone. Watch the uvicorn console:
- factual asks → auto-sent
- rate/submission/resume asks → queued as a draft

Approve drafts anytime:
```bash
python review.py
```

## The 24-hour rule
Free-form text replies only work within **24h** of the vendor's last message. For
proactive outreach outside that window, create a **message template** in the Meta UI,
wait for approval, then send with `whatsapp.send_template(...)`.

## Going to production
Deploy `app.py` to Railway/Render/a VPS (always-on HTTPS), set the same env vars, and
point the Meta callback URL at the deployed domain instead of ngrok. Consider replacing
the `review.py` CLI with a WhatsApp-based approval flow (you reply "ok" to approve).

## Safety
- `never_share` in `rules.json` blocks SSN/DOB/visa docs even if a vendor asks.
- `ALLOWED_SENDERS` in `.env` can restrict who the agent responds to while testing.
- Auto-send is limited to factual topics above `min_confidence`; everything sensitive
  is drafted for human review.
