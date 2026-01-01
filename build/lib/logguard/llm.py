from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "❌ GROQ_API_KEY is missing!\n"
        "Please set it in your environment or create a .env file.\n"
        "Example: export GROQ_API_KEY='gsk_...'"
    )

client = Groq(api_key=api_key)

def call_llm(system_prompt, user_prompt, model="llama-3.3-70b-versatile", json_mode=False):
    kwargs = {
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            }
        ],
        "model": model,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    chat_completion = client.chat.completions.create(**kwargs)
    return chat_completion.choices[0].message.content

