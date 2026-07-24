"""Load consultant profiles bundled with this project.

Each consultant is one JSON file in the ./consultants/ folder (already
sanitized — no credentials or sheet IDs). Point CONSULTANTS_DIR at another
folder to override.
"""
import json
import os
from pathlib import Path

CONSULTANTS_DIR = Path(
    os.environ.get("CONSULTANTS_DIR", Path(__file__).resolve().parent / "consultants")
)


def load_consultants():
    """Return a list of consultant dicts for use in prompts."""
    out = []
    if not CONSULTANTS_DIR.exists():
        return out
    for p in sorted(CONSULTANTS_DIR.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def consultants_summary():
    """Compact text block describing available consultants for the system prompt."""
    lines = []
    for c in load_consultants():
        lines.append(
            f"- {c.get('name','?')} | {c.get('role','?')} | {c.get('visa','?')} | "
            f"{c.get('experience_years','?')} yrs | {c.get('location','?')} | "
            f"Skills: {c.get('skills','?')}"
        )
    return "\n".join(lines) if lines else "(no consultants loaded)"


if __name__ == "__main__":
    print(consultants_summary())