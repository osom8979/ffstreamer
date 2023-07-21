#!/usr/bin/env bash

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" || exit; pwd)

"$ROOT_DIR/run" -c -d -vv --use-uvloop run \
    rtsp://admin:1234@192.168.0.138/stream1 \
    rtsp://localhost:8554/stream \
    @bytes2numpy ! \
    @grayscale ! \
    @numpy2bytes
