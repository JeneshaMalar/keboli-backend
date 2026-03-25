import contextlib
import subprocess


class PCMTranscoder:
    def __init__(self) -> None:
        self._proc: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
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
        if not self._proc or not self._proc.stdin:
            return
        self._proc.stdin.write(data)
        self._proc.stdin.flush()

    def read(self, n: int = 4096) -> bytes:
        if not self._proc or not self._proc.stdout:
            return b""
        return self._proc.stdout.read(n)

    def close(self) -> None:
        if not self._proc:
            return
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
        except Exception:
            pass
        try:
            if self._proc.stdout:
                self._proc.stdout.close()
        except Exception:
            pass
        with contextlib.suppress(Exception):
            self._proc.terminate()
        self._proc = None
