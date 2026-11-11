#!/usr/bin/env python3
"""
Your 'training loop'.

  python review.py            rate the suggestions from your last session (1-5)
  python review.py --export   turn your good ratings (4-5) into finetune.jsonl for fine-tuning later

Ratings are saved to examples.jsonl. convo_coach.py feeds the best-matching rated examples back
into the LLM prompt as few-shot examples, so the coach adapts to your taste after every review.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
LOG, EXAMPLES, OUT = HERE / "session_log.jsonl", HERE / "examples.jsonl", HERE / "finetune.jsonl"

FT_SYSTEM = ("You are a live conversation coach for a nervous person at a networking event. "
             "Reply with one short, natural thing they could say (max 80 characters).")


def review():
    if not LOG.exists():
        sys.exit("No session_log.jsonl yet - run convo_coach.py first.")
    entries = [json.loads(line) for line in LOG.read_text().splitlines() if line.strip()]
    done, quit_early = 0, False
    with EXAMPLES.open("a") as out:
        for entry in entries:
            print("\n" + "=" * 60)
            print("HEARD:", entry["heard"] or "(conversation had not started)")
            for s in entry["suggestions"]:
                r = input(f"  [{s['type']}] {s['text']}\n  rate 1-5 (Enter = skip, q = quit): ").strip().lower()
                if r == "q":
                    quit_early = True
                    break
                if r in {"1", "2", "3", "4", "5"}:
                    out.write(json.dumps({"heard": entry["heard"], "type": s["type"],
                                          "suggestion": s["text"], "rating": int(r)}) + "\n")
            if quit_early:
                break
            done += 1
    remaining = entries[done:]  # keep unreviewed entries for next time
    if remaining:
        LOG.write_text("".join(json.dumps(e) + "\n" for e in remaining))
    else:
        LOG.unlink()
    print(f"\nSaved. {len(remaining)} entries left to review.")


def export():
    rows = [json.loads(line) for line in EXAMPLES.read_text().splitlines() if line.strip()]
    good = [r for r in rows if r["rating"] >= 4]
    with OUT.open("w") as f:
        for r in good:
            f.write(json.dumps({"messages": [
                {"role": "system", "content": FT_SYSTEM},
                {"role": "user", "content": f"Type: {r['type']}\nHeard: {r['heard'] or '(nothing yet)'}"},
                {"role": "assistant", "content": r["suggestion"]},
            ]}) + "\n")
    print(f"Wrote {len(good)} training examples to {OUT}")
    if len(good) < 200:
        print("Tip: aim for 200-500+ well-rated examples before fine-tuning is worth it.")


if __name__ == "__main__":
    export() if "--export" in sys.argv else review()
