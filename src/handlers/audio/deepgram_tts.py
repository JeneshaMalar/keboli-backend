import os
import time

import httpx

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
    _now_ms()
    first_byte_ms: int | None = None
    out = bytearray()
    async with httpx.AsyncClient(timeout=None) as client, client.stream(
        "POST", url, headers=headers, json={"text": text}
    ) as r:
        r.raise_for_status()
        async for chunk in r.aiter_bytes():
            if not chunk:
                continue
            if first_byte_ms is None:
                first_byte_ms = _now_ms()
            out.extend(chunk)

    return bytes(out)
