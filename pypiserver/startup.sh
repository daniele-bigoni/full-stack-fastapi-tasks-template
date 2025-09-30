#!/usr/bin/env bash

PWD_PATH="$PWD"
PKGS_PATH=$1
OUT_PATH=$2

for dir in $PKGS_PATH/*/
do
  cd $dir \
    && uv build -o "${PWD_PATH}/${OUT_PATH}" \
    && cd $PWD_PATH
done