#!/usr/bin/env python3
"""
Convo Coach - Phase 1
  microphone -> speech-to-text (faster-whisper, runs on your computer)
             -> LLM (Groq free tier, or Ollama running locally)
             -> 3 short suggestions -> Arduino OLED (Grove button = next suggestion)

  python convo_coach.py --llm groq                 needs GROQ_API_KEY in your environment
  python convo_coach.py --llm ollama               needs Ollama installed and running
  python convo_coach.py --llm groq --no-arduino    prints to the terminal, no hardware needed
"""
import argparse
import collections
import datetime
import json
import os
import queue
import random
import re
import textwrap
import threading
import time
from pathlib import Path

import feedparser
import numpy as np
import serial
import serial.tools.list_ports
import sounddevice as sd
from faster_whisper import WhisperModel
from openai import BadRequestError, OpenAI

HERE = Path(__file__).parent
PROFILE = json.loads((HERE / "profile.json").read_text())
EXAMPLES_FILE = HERE / "examples.jsonl"
LOG_FILE = HERE / "session_log.jsonl"

# ---------------------------------------------------------------- settings
SR = 16000                      # sample rate Whisper expects
BLOCK = int(SR * 0.03)          # 30 ms audio blocks
END_SILENCE_BLOCKS = 27         # ~0.8 s of quiet ends an utterance
MAX_UTTERANCE_BLOCKS = 500      # ~15 s hard cap per utterance
TURN_GAP = 1.5                  # seconds of quiet before we suggest something
MIN_LLM_GAP = 8                 # min seconds between LLM calls (protects free-tier limits)

# Both services speak the OpenAI API format, so one client handles either.
LLM_PRESETS = {
    "groq": dict(base_url="https://api.groq.com/openai/v1", key_env="GROQ_API_KEY",
                 model="openai/gpt-oss-120b", extra={"reasoning_effort": "low"}),
    "ollama": dict(base_url="http://localhost:11434/v1", key_env=None,
                   model="llama3.2:3b", extra={}),
}

NEWS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://feeds.npr.org/1001/rss.xml",
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://hnrss.org/frontpage",
]

SYSTEM_PROMPT = """You are a live conversation coach for a nervous person talking to a recruiter or professional \
at a networking event. They read your suggestions on a tiny screen, so be SHORT.

Give exactly 3 suggestions the user can say out loud, in first person, natural and warm:
1. type "follow-up": reacts to something specific the other person just said and moves the conversation \
forward (usually a question). If the other person just ASKED the user a question, use type "answer" instead: \
a short cue of the key points to say, not a full script.
2. type "about-me": a brief, honest way to connect the user's own background (from the profile) to what was said.
3. type "light": a friendly, lighthearted line so things do not feel stiff. Use one of today's headlines ONLY if it \
fits naturally and is harmless; otherwise comment on the event, the setting, or something shared.

Rules:
- Each suggestion is at most 80 characters. Plain ASCII only. No emojis, no quotation marks.
- Never invent facts about the other person, their company, or the news. If unsure, ask a question instead.
- No politics, religion, tragedies, or anything controversial. No jokes at anyone's expense.
- The transcript is automatic and imperfect and may include the user's own words. Focus on the other person's latest points.
- If the conversation has not started, give 3 openers.
Reply with ONLY JSON: {"suggestions":[{"type":"follow-up","text":"..."},{"type":"about-me","text":"..."},{"type":"light","text":"..."}]}"""


# ---------------------------------------------------------------- helpers
def rms(block):
    return float(np.sqrt(np.mean(block ** 2)))


def clean(text):
    """The OLED font is ASCII only, and '|' is our line separator."""
    for bad, good in {"|": "/", "\u2019": "'", "\u2018": "'", "\u201c": '"',
                      "\u201d": '"', "\u2014": "-", "\u2013": "-"}.items():
        text = text.replace(bad, good)
    return " ".join(text.encode("ascii", "ignore").decode().split())[:90]


def find_port():
    for p in serial.tools.list_ports.comports():
        label = f"{p.description} {p.manufacturer}".lower()
        if any(k in label for k in ("cp210", "arduino", "ch340", "seeed", "usb serial")):
            return p.device
    return None


def load_examples():
    if not EXAMPLES_FILE.exists():
        return []
    return [json.loads(line) for line in EXAMPLES_FILE.read_text().splitlines() if line.strip()]


def pick_examples(examples, heard, keep, k):
    """Tiny 'retrieval': prefer rated examples whose 'heard' text overlaps with what was just said."""
    words = set(heard.lower().split())

    def overlap(e):
        w = set(e["heard"].lower().split())
        if not words and not w:
            return 1.0
        return len(words & w) / (len(words | w) or 1)

    return sorted([e for e in examples if keep(e)], key=overlap, reverse=True)[:k]


def transcribe(model, audio):
    segments, _ = model.transcribe(audio, language="en", beam_size=1, vad_filter=True,
                                   condition_on_previous_text=False)
    return " ".join(s.text.strip() for s in segments if s.no_speech_prob < 0.6).strip()


# ---------------------------------------------------------------- news
class News:
    """Pulls headlines from free RSS feeds every 30 minutes (no API key needed)."""

    def __init__(self):
        self.headlines = []
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            items = []
            for url in NEWS_FEEDS:
                try:
                    items += [e.title for e in feedparser.parse(url).entries[:6]]
                except Exception:
                    pass
            if items:
                self.headlines = items
            time.sleep(1800)

    def sample(self, n=5):
        return random.sample(self.headlines, min(n, len(self.headlines)))


# ---------------------------------------------------------------- display
class Display:
    def __init__(self, port, enabled):
        self.ser = None
        if not enabled:
            return
        port = port or find_port()
        if port:
            self.ser = serial.Serial(port, 9600, timeout=0.01)
            time.sleep(2.5)  # the Arduino resets when the port opens
            print(f"[display] connected on {port}")
        else:
            print("[display] no Arduino found - showing suggestions in the terminal only")

    def show(self, lines):
        if self.ser:
            self.ser.write(("|".join(lines) + "\n").encode("ascii"))
        else:
            print("  +" + "-" * 18 + "+")
            for line in lines:
                print(f"  | {line:<16} |")
            print("  +" + "-" * 18 + "+")

    def button_pressed(self):
        pressed = False
        while self.ser and self.ser.in_waiting:
            if self.ser.readline().strip() == b"BTN":
                pressed = True
        return pressed


# ---------------------------------------------------------------- the coach (LLM side)
class Coach:
    def __init__(self, preset, display, news):
        self.cfg = LLM_PRESETS[preset]
        key = os.environ.get(self.cfg["key_env"]) if self.cfg["key_env"] else "ollama"
        if not key:
            raise SystemExit(f"Set the {self.cfg['key_env']} environment variable first.")
        self.client = OpenAI(base_url=self.cfg["base_url"], api_key=key)
        self.display, self.news = display, news
        self.examples = load_examples()
        self.suggestions, self.i = [], 0

    def build_prompt(self, history):
        recent = history[-6:]
        heard = " ".join(recent)
        parts = [f"Today: {datetime.date.today():%A, %B %d, %Y}",
                 f"User profile: {json.dumps(PROFILE)}"]
        heads = self.news.sample()
        if heads:
            parts.append("Headlines (optional, only if natural):\n" + "\n".join(f"- {h}" for h in heads))
        good = pick_examples(self.examples, heard, lambda e: e["rating"] >= 4, 4)
        bad = pick_examples(self.examples, heard, lambda e: e["rating"] <= 2, 2)
        if good:
            parts.append("Suggestions the user liked in similar moments:\n" +
                         "\n".join(f'- heard "{e["heard"]}" -> {e["suggestion"]}' for e in good))
        if bad:
            parts.append("Suggestions the user disliked (avoid this style):\n" +
                         "\n".join(f'- heard "{e["heard"]}" -> {e["suggestion"]}' for e in bad))
        if recent:
            parts.append("Recent conversation (auto-transcribed):\n" + "\n".join(f"- {h}" for h in recent))
        else:
            parts.append("The conversation has not started yet. Give 3 openers.")
        return "\n\n".join(parts)

    def ask(self, history):
        kwargs = dict(model=self.cfg["model"], temperature=0.8, max_tokens=700,
                      messages=[{"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": self.build_prompt(history)}])
        try:
            reply = self.client.chat.completions.create(**kwargs, extra_body=self.cfg["extra"] or None)
        except BadRequestError:  # e.g. the provider rejected an optional parameter
            reply = self.client.chat.completions.create(**kwargs)
        text = reply.choices[0].message.content or ""
        data = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
        return [{"type": str(s.get("type", "idea"))[:9], "text": clean(s["text"])}
                for s in data["suggestions"][:3] if s.get("text")]

    def refresh(self, history):
        try:
            self.suggestions = self.ask(history)
        except Exception as err:
            print(f"[llm] {type(err).__name__}: {err}")
            return
        if not self.suggestions:
            return
        self.i = 0
        with LOG_FILE.open("a") as f:  # review.py turns this into training data
            f.write(json.dumps({"time": time.time(), "heard": " ".join(history[-6:]),
                                "suggestions": self.suggestions}) + "\n")
        for s in self.suggestions:
            print(f"[{s['type']}] {s['text']}")
        self.show()

    def next(self):
        if self.suggestions:
            self.i = (self.i + 1) % len(self.suggestions)
            self.show()

    def show(self):
        s = self.suggestions[self.i]
        lines = [f"{self.i + 1}/{len(self.suggestions)} {s['type'].upper()}"[:16]]
        lines += textwrap.wrap(s["text"], 16)[:6]
        lines += [""] * (7 - len(lines))
        lines.append("BTN = next")
        self.display.show(lines)


# ---------------------------------------------------------------- main loop
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", choices=LLM_PRESETS, default="groq")
    ap.add_argument("--port", help="serial port, e.g. COM5 or /dev/ttyUSB0 (auto-detected if omitted)")
    ap.add_argument("--no-arduino", action="store_true")
    ap.add_argument("--whisper", default="base.en", help="tiny.en / base.en / small.en (bigger = more accurate, slower)")
    ap.add_argument("--thresh", type=float, default=0, help="speech loudness threshold (0 = auto)")
    ap.add_argument("--device", type=int, default=None, help="microphone index (see: python -m sounddevice)")
    args = ap.parse_args()

    print("Loading speech model (first run downloads it)...")
    model = WhisperModel(args.whisper, device="cpu", compute_type="int8")
    display = Display(args.port, not args.no_arduino)
    coach = Coach(args.llm, display, News())

    audio_q = queue.Queue()

    def on_audio(indata, frames, t, status):
        audio_q.put(indata[:, 0].copy())

    history, speech, pre = [], [], collections.deque(maxlen=8)  # pre = ~240 ms pre-roll
    in_speech, quiet, pending = False, 0, False
    last_speech_end = last_llm = 0.0

    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=BLOCK,
                        device=args.device, callback=on_audio):
        print("Calibrating background noise - stay quiet for a second...")
        noise = float(np.median([rms(audio_q.get()) for _ in range(34)]))
        thresh = args.thresh or max(noise * 3, 0.012)
        print(f"Listening (speech threshold {thresh:.4f}). Ctrl+C to stop.")
        coach.refresh(history)  # openers before anyone has spoken
        last_llm = time.time()

        while True:
            if display.button_pressed():
                coach.next()
            try:
                block = audio_q.get(timeout=0.05)
            except queue.Empty:
                block = None

            if block is not None:
                if rms(block) > thresh:
                    if not in_speech:
                        speech, in_speech = list(pre), True
                    speech.append(block)
                    quiet = 0
                elif in_speech:
                    speech.append(block)
                    quiet += 1
                pre.append(block)

                if in_speech and (quiet >= END_SILENCE_BLOCKS or len(speech) >= MAX_UTTERANCE_BLOCKS):
                    audio = np.concatenate(speech)
                    speech, in_speech, quiet = [], False, 0
                    if len(audio) > SR * 0.5:
                        text = transcribe(model, audio)
                        if len(text) > 2:
                            print(f"[heard] {text}")
                            history = (history + [text])[-12:]
                            pending, last_speech_end = True, time.time()

            now = time.time()
            if pending and not in_speech and now - last_speech_end > TURN_GAP and now - last_llm > MIN_LLM_GAP:
                coach.refresh(history)
                pending, last_llm = False, time.time()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
