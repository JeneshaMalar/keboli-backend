FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=mwader/static-ffmpeg:latest /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:latest /ffprobe /usr/local/bin/

COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache -r pyproject.toml

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]