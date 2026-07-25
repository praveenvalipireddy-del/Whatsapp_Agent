"""Send a WhatsApp message manually.

Usage:
  python send.py 19495943404 "Hi, following up on your query..."

The recipient must be in your allowed test-recipient list (dev mode), and
you can only send free-form text within 24h of their last message to you.
"""
import sys

from dotenv import load_dotenv

load_dotenv()

import whatsapp


def main():
    if len(sys.argv) < 3:
        print('Usage: python send.py <number> "<message>"')
        print('Example: python send.py 19495943404 "Thanks, will get back to you."')
        return
    to = sys.argv[1].lstrip("+")
    body = " ".join(sys.argv[2:])
    resp = whatsapp.send_text(to, body)
    msg_id = resp.get("messages", [{}])[0].get("id", "?")
    print(f"Sent to {to}: {body}")
    print(f"  message id: {msg_id}")


if __name__ == "__main__":
    main()