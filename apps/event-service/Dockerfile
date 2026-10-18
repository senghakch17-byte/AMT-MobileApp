# 1. Start with a fast, pre-built Rust/Python engine image
FROM ghcr.io/astral-sh/uv:python3.12-alpine

# 2. Set the working directory inside your virtual container environment
WORKDIR /backend

# Keep container environment separate from any copied local .venv.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# 3. Copy only dependency files first to lock down layer caching
COPY pyproject.toml uv.lock ./

# 4. Install python dependencies cleanly using uv
RUN uv sync --frozen --no-cache --no-install-project

# 5. Copy the application into the working directory
COPY . .

# 6. Tell Docker to open up Port 8001
EXPOSE 8001

# 7. Start the API server using uv's managed environment
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]    