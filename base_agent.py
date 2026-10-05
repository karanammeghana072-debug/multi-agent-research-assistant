import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PREFERRED = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
]
SKIP = ("whisper", "tts", "guard", "orpheus", "safeguard", "compound")
_model = None


def get_model():
    global _model
    if _model:
        return _model
    if os.getenv("GROQ_MODEL"):
        _model = os.getenv("GROQ_MODEL")
        return _model
    ids = [m.id for m in client.models.list().data]
    for name in PREFERRED:
        if name in ids:
            _model = name
            return _model
    chat = [i for i in ids if not any(s in i for s in SKIP)]
    if not chat:
        raise RuntimeError("No chat model available for this Groq API key.")
    _model = chat[0]
    return _model


class Agent:
    def __init__(self, name, role):
        self.name = name
        self.role = role

    def run(self, task):
        print(f"[{self.name}] working...")
        response = client.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": self.role},
                {"role": "user", "content": task},
            ],
        )
        return response.choices[0].message.content