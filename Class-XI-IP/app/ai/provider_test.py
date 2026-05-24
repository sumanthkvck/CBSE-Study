"""Quick test — run directly to check provider is working."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.ai.provider import ask, has_any_key, active_provider, OFFLINE_MSG

print(f"Active provider: {active_provider()}")
print(f"Has key: {has_any_key()}")
response = ask("What is a variable in Python? (one sentence)")
print(f"Response: {response[:200]}")
if response == OFFLINE_MSG:
    print("(Offline mode — set GEMINI_API_KEY to enable AI)")
else:
    print("AI provider working correctly!")
