#!/usr/bin/env bash

ffplay \
    -fflags nobuffer \
    -fflags discardcorrupt \
    -flags low_delay \
    -framedrop \
    -avioflags direct \
    -rtsp_transport tcp \
    rtsp://localhost:8554/stream
