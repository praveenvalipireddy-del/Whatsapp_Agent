"""CLI to review pending drafts: approve (send), edit, or reject.

Usage:  python review.py
"""
from dotenv import load_dotenv

load_dotenv()

import store
import whatsapp

store.init()


def main():
    drafts = store.pending_drafts()
    if not drafts:
        print("No pending drafts.")
        return

    for d in drafts:
        print("\n" + "=" * 60)
        print(f"Draft #{d['id']}  ->  {d['wa_id']}   [{d['topic']}]")
        print("-" * 60)
        print(d["body"])
        print("-" * 60)
        choice = input("[s]end / [e]dit & send / [r]eject / [skip]: ").strip().lower()

        if choice == "s":
            whatsapp.send_text(d["wa_id"], d["body"])
            store.add_message(d["wa_id"], "agent", d["body"])
            store.set_draft_status(d["id"], "sent")
            print("Sent.")
        elif choice == "e":
            new = input("New text: ").strip()
            if new:
                whatsapp.send_text(d["wa_id"], new)
                store.add_message(d["wa_id"], "agent", new)
                store.set_draft_status(d["id"], "sent")
                print("Sent edited reply.")
        elif choice == "r":
            store.set_draft_status(d["id"], "rejected")
            print("Rejected.")
        else:
            print("Skipped.")


if __name__ == "__main__":
    main()
