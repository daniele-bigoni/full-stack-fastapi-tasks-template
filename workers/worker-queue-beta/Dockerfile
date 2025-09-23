FROM python:3.13 AS base

ARG TZ
ENV TZ=$TZ

WORKDIR /app/

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false


FROM base AS install

# Copy poetry.lock* in case it doesn't exist in the repo
# COPY ./pyproject.toml ./poetry.lock* /app/
# We avoid using the poetry lock to disentangle from the potential use of local vs remote private pypi
COPY pyproject.toml /app/

# Add private pypi repo as first choice
ARG PRIVATE_PYPI_HOST
ARG PRIVATE_PYPI_PORT
ARG PRIVATE_PYPI_INDEX
RUN poetry source add --priority=primary private-pypi "http://$PRIVATE_PYPI_HOST:$PRIVATE_PYPI_PORT/$PRIVATE_PYPI_INDEX/"


# Install dependencies
RUN poetry install --no-root


FROM install AS release

COPY worker /app/worker

#ENTRYPOINT ["tail", "-f", "/dev/null"]
ENTRYPOINT celery -A worker.main worker -l INFO -Q shared,beta