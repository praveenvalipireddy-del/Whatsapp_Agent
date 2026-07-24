# Deploying to production (Render free tier)

The webhook host is independent of the WhatsApp phone number — you can deploy and
verify the server now, and register a real number later.

## A. Deploy the server (do this anytime)

1. Push this repo to GitHub (if not already).
2. Go to https://render.com → sign up (free) → **New + → Blueprint**.
3. Connect your GitHub repo. Render reads `whatsapp_agent/render.yaml`.
4. It creates the service. Before first deploy, open **Environment** and set the
   secret values (these are `sync: false` in the blueprint, so Render prompts you):
   - `PHONE_NUMBER_ID`   → your WhatsApp phone number ID
   - `WHATSAPP_TOKEN`    → permanent token
   - `VERIFY_TOKEN`      → the bs_... string from your local .env
   - `APP_SECRET`        → leave blank to skip signature check, or set the real one
   - `OPENROUTER_API_KEY`→ your sk-or-v1-... key
   - `ALLOWED_SENDERS`   → leave blank
5. Deploy. When it's live you'll get a URL like `https://bench-sales-whatsapp.onrender.com`.
6. Point Meta's webhook Callback URL at `https://<that-url>/webhook` with the same
   VERIFY_TOKEN, and re-subscribe to `messages` (same steps as ngrok setup).

Free-tier caveats: the service sleeps after 15 min idle (first message wakes it,
~50s; Meta retries so it still lands) and the SQLite draft DB resets on redeploy.
Upgrade to the $7/mo Starter plan to remove both.

## B. Register a real phone number (when you have one)

Requirement: a number NOT currently active on any WhatsApp account (registering it
to Cloud API disables its use in the normal WhatsApp app).

1. Meta app → **WhatsApp → Step 2. Production setup → Register your WhatsApp phone number**.
2. Fill business info, choose the number, verify by SMS/call.
3. Set its display name (needs approval, usually quick).
4. Update `PHONE_NUMBER_ID` in Render env to the new number's ID.

## C. Go Live + billing

1. **App settings → Basic** → add a **Privacy Policy URL** (required to flip Live).
2. Toggle **App Mode → Live** (top of dashboard).
3. **WhatsApp → Step 2 → Add payment method** (WhatsApp bills per conversation).
4. Optional but recommended: complete **Business verification** to lift the
   250-conversation/day starter cap.

After Live + a registered number, the agent can message any vendor with no
allow-list — full production.
