import os
import httpx
import time
from typing import Optional
from src.config.settings import settings


def _now_ms() -> int:
    return int(time.time() * 1000)


async def deepgram_tts_bytes(text: str) -> bytes:
    model = os.getenv("DEEPGRAM_TTS_MODEL", "aura-helios-en")
    url = f"https://api.deepgram.com/v1/speak?model={model}&encoding=mp3"

    headers = {
        "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
        "Content-Type": "application/json",
    }
    print(f"Deepgram TTS request prepared with model '{model}' and text length {len(text)}")
    start = _now_ms()
    first_byte_ms: Optional[int] = None
    out = bytearray()
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, headers=headers, json={"text": text}) as r:
            r.raise_for_status()
            async for chunk in r.aiter_bytes():
                if not chunk:
                    continue
                if first_byte_ms is None:
                    first_byte_ms = _now_ms()
                    print(f"TTS Time to First Byte (TTFB): {first_byte_ms - start}ms")
                out.extend(chunk)

    return bytes(out)