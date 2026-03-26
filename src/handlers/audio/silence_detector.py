"""Silence detection notifier for real-time interview sessions."""

import asyncio
import json
import time
from collections.abc import Callable


def now_ms() -> int:
    """Return the current time in milliseconds since epoch."""
    return int(time.time() * 1000)


async def silence_notifier(ws: object, get_last_speech: Callable[[], int | None]) -> None:
    """Continuously monitor for silence and notify the client via WebSocket.

    Sends a SILENCE_DETECTED message when the candidate has been
    silent for more than 500ms, throttled to one notification per 500ms.

    Args:
        ws: WebSocket connection to send silence notifications on.
        get_last_speech: Callable returning the timestamp (ms) of last detected speech.
    """
    last_silence_sent: int | None = None

    while True:
        await asyncio.sleep(0.25)

        last_speech = get_last_speech()
        if last_speech is None:
            continue

        silence_ms = now_ms() - last_speech

        if silence_ms < 500:
            continue

        if last_silence_sent and silence_ms - last_silence_sent < 500:
            continue

        last_silence_sent = silence_ms

        await ws.send_text(
            json.dumps({"type": "SILENCE_DETECTED", "silence_ms": silence_ms})
        )
