#!/bin/bash
# Pull kernel console log from diting userdata partition
# The kernel writes a 4 MiB ring buffer to the last 1025 blocks (4 KiB each) of userdata

set -euo pipefail

OUT_FILE="${1:-logs/boot.txt}"
LOG_SIZE=$((4 * 1024 * 1024))  # 4 MiB
BLOCK_SIZE=4096
BLOCK_COUNT=1025

echo "Pulling ${LOG_SIZE} bytes from userdata..."

# userdata partition on diting
USERDATA="/dev/block/by-name/userdata"

# Read the last LOG_SIZE bytes
adb exec-out "dd if=${USERDATA} bs=${BLOCK_SIZE} skip=\$(( \$(blockdev --getsz ${USERDATA}) - ${BLOCK_COUNT} )) count=${BLOCK_COUNT}" | \
    python3 -c "
import sys, struct
data = sys.stdin.buffer.read()
# Find the log header: 'SWEET LOG:' or 'DITING LOG:'
header = b'DITING LOG:'
idx = data.rfind(header)
if idx == -1:
    header = b'SWEET LOG:'
    idx = data.rfind(header)
if idx == -1:
    print('No log header found', file=sys.stderr)
    sys.exit(1)
# Parse: header + 8-byte sequence + 8-byte timestamp + 4-byte length
# Then the log data
log_start = idx + len(header)
# Skip sequence/timestamp (16 bytes)
log_data = data[log_start + 16:]
sys.stdout.buffer.write(log_data)
" > "${OUT_FILE}"

echo "Log saved to ${OUT_FILE} ($(wc -c < "${OUT_FILE}") bytes)"