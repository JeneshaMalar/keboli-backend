import os
import time
from typing import Optional
from src.config.settings import settings
from groq import AsyncGroq


class GroqLLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        self._api_key = api_key or settings.GROQ_API_KEY
        if not self._api_key:
            raise ValueError("GROQ_API_KEY is not set")

        self._client = AsyncGroq(api_key=self._api_key)
        default_model = getattr(settings, "GROQ_MODEL", None) or os.getenv("GROQ_MODEL")
        self._model = model or default_model or "llama-3.3-70b-versatile"
        self._system_prompt = system_prompt or os.getenv(
            "GROQ_SYSTEM_PROMPT",
            "You are a helpful assistant. Answer the user's question as concisely as possible.keep the answer very short and to the point.",
        )

    async def generate(self, user_text: str) -> str:
        start_ms = int(time.time() * 1000)

        completion = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=0,
        )

        out = (completion.choices[0].message.content or "").strip()
        elapsed_ms = int(time.time() * 1000) - start_ms
        print(f"Groq LLM ({elapsed_ms}ms): {out}")
        return out
