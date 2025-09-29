#!/usr/bin/env bash

set -a; source .env; set +a

PWD_PATH="$PWD"
EXEC_PATH="$(dirname -- "${BASH_SOURCE[0]}")"
PKGS_PATH="$EXEC_PATH/packages"

for dir in $PKGS_PATH/*/
do
  cd $dir \
    && uv build -o "dist/" \
    && uv publish --publish-url "http://$PRIVATE_PYPI_HOST:$PRIVATE_PYPI_PORT/" --verbose --username admin --password admin dist/* \
    && cd $PWD_PATH
done