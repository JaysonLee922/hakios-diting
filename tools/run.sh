#!/bin/bash
# Run boot image on diting device and collect logs
# Usage: run.sh <label> <timeout_seconds>

set -euo pipefail

LABEL="${1:-daily}"
TIMEOUT="${2:-120}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVICE_DIR="$(dirname "$SCRIPT_DIR")"
OUT_DIR="${DEVICE_DIR}/out"
LOGS_DIR="${DEVICE_DIR}/logs"

mkdir -p "${LOGS_DIR}"

BOOT_IMG="${OUT_DIR}/shim-boot-${LABEL}.img"
if [[ ! -f "${BOOT_IMG}" ]]; then
    echo "Boot image not found: ${BOOT_IMG}" >&2
    echo "Run build-image.sh first" >&2
    exit 1
fi

echo "Booting ${BOOT_IMG} on device..."
echo "Timeout: ${TIMEOUT}s"

# Check device is in fastboot
if ! fastboot devices | grep -q "fastboot"; then
    echo "Device not in fastboot mode" >&2
    echo "Hold Power+VolDown to enter fastboot" >&2
    exit 1
fi

# Boot the image
fastboot boot "${BOOT_IMG}"

# Wait for boot
echo "Waiting for boot (${TIMEOUT}s)..."
sleep "${TIMEOUT}"

# Try to pull logs via USB networking (if enabled)
LOG_FILE="${LOGS_DIR}/boot-${LABEL}.txt"
echo "Attempting to pull logs..."

# Method 1: USB networking (if ditingusb=2)
if timeout 10 nc -uz 192.168.7.2 5140 2>/dev/null; then
    echo "USB network up, pulling live log..."
    nc -ul 5140 > "${LOG_FILE}" &
    NC_PID=$!
    sleep 2
    kill $NC_PID 2>/dev/null
    echo "Log saved to ${LOG_FILE}"
else
    # Method 2: Recovery mode log pull
    echo "USB network not up, trying recovery mode..."
    echo "Please hold Power+VolDown to enter fastboot, then press Enter..."
    read -r

    if fastboot devices | grep -q "fastboot"; then
        fastboot boot recovery/recovery.img
        echo "Waiting for adb..."
        while ! adb shell true 2>/dev/null; do sleep 1; done

        echo "Pulling kernel log from userdata..."
        "${DEVICE_DIR}/tools/diting-log-pull.sh" "${LOG_FILE}"

        adb reboot bootloader
    fi
fi

echo "Done. Log: ${LOG_FILE}"