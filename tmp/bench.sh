#!/usr/bin/env sh
# Benchmark every model in ./tmp — extremely simple.
#
# Usage: put *.gguf files in ./tmp (flat, no subfolders), then run:
#   sh tmp/bench.sh
#
# The llama-bench command below is FIXED (phone-safe profile): only the -m
# model path changes from one run to the next. Every result is APPENDED to
# ./tmp/bench.txt — reruns just keep adding to the bottom.
#
# Edit the BB= line to change the fixed flags (see docs/termux.md).
set -eu

REPORT=tmp/bench.txt
BB="llama-bench -p 512 -n 128 -t 4 -tb 4 -r 3 --delay 5"

found=0
for model in tmp/*.gguf; do
    [ -e "$model" ] || continue
    found=1
    printf '\n########## %s ##########\n\n' "$model" >> "$REPORT"
    $BB -m "$model" >> "$REPORT"
done

if [ "$found" = 0 ]; then
    echo "no *.gguf files in tmp/ — drop your models there first"
    exit 1
fi

echo "done. results appended to $REPORT"
