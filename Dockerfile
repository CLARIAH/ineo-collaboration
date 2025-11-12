FROM python:3.12-alpine
COPY --from=ghcr.io/astral-sh/uv:0.9.8 /uv /uvx /bin/

RUN apk add --no-cache \
    bash \
    curl \
    git \
    wget

ADD . /app
WORKDIR /app
RUN uv sync --locked

CMD ["sleep", "infinity"]
