# 1. Start with a fast, pre-built uv + Python image
FROM ghcr.io/astral-sh/uv:python3.12-alpine

# 2. Set the working directory inside the container
WORKDIR /backend

ENV UV_CACHE_DIR=/tmp/uv-cache

# 3. Copy only dependency files first to lock down layer caching
COPY pyproject.toml uv.lock ./

# 4. Install python dependencies cleanly using uv (runtime deps only)
RUN uv sync --frozen --no-cache --no-install-project --no-dev

# 5. Copy the application into the working directory
COPY . .

# 6. Tell Docker to open up Port 8003
EXPOSE 8003

# 7. Start the API server using uv's managed environment
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
