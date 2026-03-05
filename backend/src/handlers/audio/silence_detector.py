import asyncio
import time
import json

def now_ms():
    return int(time.time() * 1000)

async def silence_notifier(ws, get_last_speech):
    last_silence_sent = None

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

        await ws.send_text(json.dumps({
            "type": "SILENCE_DETECTED",
            "silence_ms": silence_ms
        }))