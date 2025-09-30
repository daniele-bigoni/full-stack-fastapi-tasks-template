FROM pypiserver/pypiserver:latest

RUN apk add apache2-utils

RUN htpasswd -c -b /.htpasswd admin admin

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

COPY packages /src/packages
COPY startup.sh /src/startup.sh

WORKDIR /

RUN /src/startup.sh /src/packages /data/packages

CMD ["run","-a","update","-p","8082","-P","/.htpasswd","--overwrite","/data/packages/"]