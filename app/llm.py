from groq import Groq
import os

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def call_llm(system_prompt: str, user_prompt: str, model: str = "openai/gpt-oss-120b"):
    """
    Generic LLM call wrapper for Groq
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0
    )

    return response.choices[0].message.content
