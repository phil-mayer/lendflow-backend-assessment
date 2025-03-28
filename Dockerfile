# Python 3.12 with uv preinstalled.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm

# 
RUN apt-get update && apt-get install -y --no-install-recommends 

# The `/app` directory will be used for the application.
WORKDIR /app

# Enable bytecode compilation.
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume.
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Add the rest of the project source code and create a virtualenv. Doing this separately from dependency installation
# allows optimal layer caching.
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Place executables in the environment at the front of the path.
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint.
ENTRYPOINT []

# Run the Django application by default. By running `uv sync` above, a virtualenv will have been created which includes
# the `python` executable.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
