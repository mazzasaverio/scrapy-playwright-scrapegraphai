FROM python:3.11
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
# Change the working directory to the `app` directory
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/scrapy.cfg ./
COPY src/crawler/ ./crawler/

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

ENV PLAYWRIGHT_BROWSERS_PATH=/playwright-browsers

RUN playwright install --with-deps chromium \
    && chmod -Rf 777 $PLAYWRIGHT_BROWSERS_PATH

CMD ["uv", "run", "scrapy", "crawl", "frontier_spider"]