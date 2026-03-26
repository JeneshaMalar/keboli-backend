"""Deepgram Speech-to-Text (STT) client using WebSocket streaming."""

import asyncio
import json
import os
from collections.abc import Callable

import websockets

from src.config.settings import settings


class DeepgramSTT:
    """Real-time speech-to-text transcription via Deepgram's WebSocket API.

    Reads PCM audio from a transcoder, streams it to Deepgram, and
    dispatches final transcripts to a callback function.

    Args:
        transcoder: A PCMTranscoder providing raw 16kHz mono audio.
    """

    def __init__(self, transcoder: object) -> None:
        self.transcoder = transcoder
        self.last_speech_ms: int | None = None
        self.transcript_parts: list[str] = []

    async def connect(self, ws: object, on_final_transcript: Callable) -> None:
        """Open a Deepgram WebSocket connection and start streaming audio.

        Runs two concurrent loops: one pumps PCM audio to Deepgram,
        the other reads transcript messages and forwards finals to the callback.

        Args:
            ws: The client-facing WebSocket to send interim/final results.
            on_final_transcript: Async callback invoked with (full_text, confidence).
        """
        model = os.getenv("DEEPGRAM_STT_MODEL", "nova-2")
        language = os.getenv("DEEPGRAM_LANGUAGE", "en-US")
        endpointing = os.getenv("DEEPGRAM_ENDPOINTING_MS", "300")

        dg_url = (
            "wss://api.deepgram.com/v1/listen"
            f"?model={model}"
            f"&language={language}"
            "&encoding=linear16"
            "&sample_rate=16000"
            "&channels=1"
            "&punctuate=true"
            "&smart_format=true"
            "&interim_results=true"
            f"&endpointing={endpointing}"
        )

        headers = {"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}
        async with websockets.connect(dg_url, extra_headers=headers) as dg_ws:

            async def pump_pcm() -> None:
                """Continuously read PCM chunks from the transcoder and send to Deepgram."""
                while True:
                    chunk = await asyncio.to_thread(self.transcoder.read, 4096)
                    if chunk:
                        await dg_ws.send(chunk)
                    else:
                        await asyncio.sleep(0.01)

            async def read_messages() -> None:
                """Process incoming Deepgram messages and dispatch final transcripts."""
                async for raw in dg_ws:
                    if not isinstance(raw, str):
                        continue

                    data = json.loads(raw)
                    ch = data.get("channel") or {}
                    alts = ch.get("alternatives") or []
                    if not alts:
                        continue

                    alt = alts[0] or {}
                    text = (alt.get("transcript") or "").strip()
                    if not text:
                        continue

                    await ws.send_text(json.dumps({"type": "INTERRUPT"}))

                    confidence = alt.get("confidence")
                    speech_final = bool(data.get("speech_final"))
                    is_final = bool(data.get("is_final"))

                    if not (speech_final or is_final):
                        await ws.send_text(
                            json.dumps({"type": "partial", "text": text})
                        )
                        continue

                    self.transcript_parts.append(text)
                    full = " ".join(self.transcript_parts).strip()
                    self.transcript_parts.clear()

                    await on_final_transcript(full, confidence)

            await asyncio.gather(pump_pcm(), read_messages())
