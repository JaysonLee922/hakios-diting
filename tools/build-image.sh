#!/bin/bash
# Build boot image for diting (Xiaomi 12T Pro)
# Usage: build-image.sh <label> <boot-args...>

set -euo pipefail

LABEL="${1:-daily}"
shift
BOOT_ARGS="$*"

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVICE_DIR="$(dirname "$SCRIPT_DIR")"
KERNEL_DIR="${DEVICE_DIR}/../hakios-xnu-kernel"
SHIM_DIR="${KERNEL_DIR}/shim"
OUT_DIR="${DEVICE_DIR}/out"

mkdir -p "${OUT_DIR}"

# Kernel image
KERNEL="${KERNEL_DIR}/xnu/out/kernel.development.diting"
if [[ ! -f "${KERNEL}" ]]; then
    echo "Kernel not found: ${KERNEL}" >&2
    echo "Build kernel first: cd ${KERNEL_DIR} && make diting_defconfig && make kernel" >&2
    exit 1
fi

# ADT
ADT="${OUT_DIR}/diting.adt"
if [[ ! -f "${ADT}" ]]; then
    echo "Building ADT..."
    python3 "${DEVICE_DIR}/tools/mkadt.py" "${ADT}" --highmem
fi

# Payload
PAYLOAD="${OUT_DIR}/payload-${LABEL}.bin"
echo "Building payload..."
python3 "${KERNEL_DIR}/tools/mkpayload.py" \
    "${KERNEL}" \
    "${ADT}" \
    "${PAYLOAD}" \
    --cmdline "${BOOT_ARGS}"

# Boot image
echo "Building boot image..."
cd "${SHIM_DIR}"
./build.sh "${PAYLOAD}"

# Copy output
BOOT_IMG="${OUT_DIR}/shim-boot-${LABEL}.img"
cp "${SHIM_DIR}/out/shim-boot.img" "${BOOT_IMG}"

echo "Boot image: ${BOOT_IMG}"
echo "Boot args: ${BOOT_ARGS}"

# Verify
python3 "${KERNEL_DIR}/tools/unpack_bootv2.py" "${BOOT_IMG}" "${OUT_DIR}/verify-${LABEL}"
cmp "${OUT_DIR}/verify-${LABEL}/ramdisk" "${PAYLOAD}" && echo "Payload verified OK" || echo "Payload verification FAILED"