#!/usr/bin/env bash

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" || exit; pwd)

"$ROOT_DIR/run" -c -d -vv run \
    rtsp://localhost:9999/live.sdp \
    rtsp://localhost:8554/stream \
    "$@"
