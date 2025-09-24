FROM python:3.13 AS base

ARG TZ
ENV TZ=$TZ

WORKDIR /app/

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/.venv/bin:$PATH"

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy


FROM base AS install

# Add private pypi repo as first choice
ARG PRIVATE_PYPI_HOST
ARG PRIVATE_PYPI_PORT
ARG PRIVATE_PYPI_INDEX
ENV UV_DEFAULT_INDEX="http://$PRIVATE_PYPI_HOST:$PRIVATE_PYPI_PORT/$PRIVATE_PYPI_INDEX/"
ENV UV_INDEX="https://pypi.org/simple"
ENV UV_INDEX_STRATEGY="first-index"

COPY README.md pyproject.toml uv.lock /app/
COPY worker /app/worker

# Sync the project
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN uv sync --frozen

#ENTRYPOINT ["tail", "-f", "/dev/null"]
ENTRYPOINT celery -A worker.main worker -l INFO -Q shared,beta