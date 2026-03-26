"""FFmpeg-based PCM audio transcoder for converting browser audio to 16kHz mono."""

import contextlib
import logging
import subprocess

logger = logging.getLogger(__name__)


class PCMTranscoder:
    """Subprocess wrapper that pipes audio through FFmpeg for format conversion.

    Converts arbitrary input audio to 16-bit signed little-endian PCM
    at 16kHz mono, suitable for speech-to-text engines.
    """

    def __init__(self) -> None:
        self._proc: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
        """Spawn the FFmpeg subprocess if not already running."""
        if self._proc is not None:
            return

        cmd = [
            "ffmpeg",
            "-loglevel",
            "quiet",
            "-i",
            "pipe:0",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "s16le",
            "pipe:1",
        ]
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )

    def write(self, data: bytes) -> None:
        """Write raw audio bytes into the FFmpeg stdin pipe.

        Args:
            data: Audio data to transcode.
        """
        if not self._proc or not self._proc.stdin:
            return
        self._proc.stdin.write(data)
        self._proc.stdin.flush()

    def read(self, n: int = 4096) -> bytes:
        """Read transcoded PCM audio from the FFmpeg stdout pipe.

        Args:
            n: Maximum number of bytes to read.

        Returns:
            Transcoded PCM audio bytes, or empty bytes if unavailable.
        """
        if not self._proc or not self._proc.stdout:
            return b""
        return self._proc.stdout.read(n)

    def close(self) -> None:
        """Shut down the FFmpeg subprocess and close all pipes."""
        if not self._proc:
            return
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
        except OSError:
            logger.debug("FFmpeg stdin already closed")
        try:
            if self._proc.stdout:
                self._proc.stdout.close()
        except OSError:
            logger.debug("FFmpeg stdout already closed")
        with contextlib.suppress(OSError):
            self._proc.terminate()
        self._proc = None
