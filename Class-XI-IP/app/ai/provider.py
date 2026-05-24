"""
AI Provider abstraction for IP Learn.
Supports Google Gemini (free default), Anthropic Claude, and OpenAI.
Falls back to offline mode if no API key is configured.
"""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Also load from user key store (set via Settings page)
_KEY_FILE = Path.home() / ".iplearn_keys"
if _KEY_FILE.exists():
    load_dotenv(_KEY_FILE, override=False)

OFFLINE_MSG = (
    "The AI Tutor needs an API key to work. "
    "Go to **Settings** to add a free Google Gemini key — it takes 2 minutes and doesn't need a credit card!"
)

SYSTEM_PROMPT = """You are a friendly, encouraging tutor for a Class XI student studying Informatics Practices (CBSE, India).

You help with these topics from the KIPS Informatics Practices textbook (Code 065):
- Chapter 1: Introduction to Computer System (hardware, software, CPU, memory, IPO cycle)
- Chapter 2: Programming with Python (history, features, IDLE, interactive vs script mode)
- Chapter 3: Python Basics (tokens, keywords, identifiers, variables, input())
- Chapter 4: Data Types and Operators (data types, mutable/immutable, typecasting, operators, precedence)
- Chapter 5: Control Flow Statements (if/elif/else, for loop, while loop, break, continue)
- Chapter 6: List Manipulation (lists, indexing, slicing, built-in methods, nested lists)
- Chapter 7: Python Dictionary (key-value pairs, dict methods, traversal)
- Chapter 8: Database Concepts (DBMS, relational model, keys, tables)
- Chapter 9: Structured Query Language (DDL, DML, SELECT, WHERE, MySQL)
- Chapter 10: Emerging Trends in Technology (AI/ML, IoT, Cloud Computing, Big Data, Blockchain)

Rules:
- Keep responses short (under 200 words) unless code is needed
- Use simple English — student is 15 years old and learning for the first time
- When explaining code, walk through it line by line
- Use Indian examples where natural (cricket, school, Aadhaar, UPI, Flipkart)
- Always be encouraging — mistakes are normal when learning
- If asked about something outside the syllabus, gently redirect to relevant topics"""


def _gemini(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    import google.generativeai as genai
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        return OFFLINE_MSG
    genai.configure(api_key=key)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system,
    )
    response = model.generate_content(prompt)
    return response.text


def _anthropic(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    import anthropic
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        return OFFLINE_MSG
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _openai(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        return OFFLINE_MSG
    client = OpenAI(api_key=key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=1024,
    )
    return resp.choices[0].message.content


def ask(prompt: str, provider: str | None = None, system: str = SYSTEM_PROMPT) -> str:
    """
    Send a prompt to the configured AI provider.

    provider: "gemini" | "anthropic" | "openai" | None (auto-detect from available keys)
    Returns the response text, or an OFFLINE_MSG if no key is available.
    """
    # Auto-detect if not specified
    if provider is None:
        if os.getenv("GEMINI_API_KEY"):
            provider = "gemini"
        elif os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        else:
            return OFFLINE_MSG

    try:
        if provider == "gemini":
            return _gemini(prompt, system)
        elif provider == "anthropic":
            return _anthropic(prompt, system)
        elif provider == "openai":
            return _openai(prompt, system)
        else:
            return OFFLINE_MSG
    except Exception as e:
        err = str(e).lower()
        if "api_key" in err or "authentication" in err or "unauthorized" in err:
            return f"❌ API key error: {e}\n\nCheck your key in **Settings**."
        if "quota" in err or "limit" in err or "429" in err:
            return "⏳ Rate limit hit — please wait a moment and try again."
        return f"❌ AI error: {e}"


def has_any_key() -> bool:
    """Returns True if at least one API key is configured."""
    return any(os.getenv(k) for k in ["GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"])


def active_provider() -> str:
    """Returns the name of the provider that will be used."""
    if os.getenv("GEMINI_API_KEY"):    return "gemini"
    if os.getenv("ANTHROPIC_API_KEY"): return "anthropic"
    if os.getenv("OPENAI_API_KEY"):    return "openai"
    return "offline"
