# Required Firmware - diting (Xiaomi 12T Pro)

**ALL firmware blobs must be extracted from YOUR device. None are included in this repo.**

## Extraction Commands

```bash
# Create firmware directories
mkdir -p fw-gpu fw-wifi fw-audio fw-bt

# GPU (Adreno 730)
adb pull /vendor/firmware/a630_zap.* fw-gpu/
adb pull /vendor/firmware/a630_gmu.* fw-gpu/
adb pull /vendor/firmware/a630_hfi.* fw-gpu/
adb pull /vendor/firmware/adreno_* fw-gpu/

# Wi-Fi (QCA6490 / ath11k)
adb pull /vendor/firmware/ath11k/ fw-wifi/
adb pull /vendor/firmware/qca/ fw-wifi/

# Audio (waipio-mtp ADSP)
adb pull /vendor/firmware/audio/ fw-audio/

# Bluetooth (QCA6490)
adb pull /vendor/firmware/qca/ fw-bt/

# Wi-Fi MAC (REQUIRED - from persist partition)
adb pull /dev/block/by-name/persist persist.img
# Mount persist.img and extract qca6490/wlan_mac.bin
# Or: adb shell 'cat /persist/qca6490/wlan_mac.bin' > fw-wifi/wlan_mac.bin
```

## Firmware Details

### GPU (Adreno 730)
| File | Purpose | Source |
|------|---------|--------|
| `a630_zap.*` | Zap shader binary (TZ authenticated) | `/vendor/firmware/` |
| `a630_gmu.*` | GMU firmware (GPU Management Unit) | `/vendor/firmware/` |
| `a630_hfi.*` | HFI firmware (Host Firmware Interface) | `/vendor/firmware/` |
| `adreno_*` | Additional Adreno blobs | `/vendor/firmware/` |

**Notes**: Same as mayfly. Zap shader requires TZ authentication. GMU manages power/clocks. HFI is command submission interface.

### Wi-Fi (QCA6490 / ath11k)
| File | Purpose | Source |
|------|---------|--------|
| `ath11k/QCA6490/hw2.0/*` | ath11k firmware (board.bin, firmware-*.bin) | `/vendor/firmware/ath11k/` |
| `qca/wlan/cnss_qca6490/*` | CNSS/QCA blobs | `/vendor/firmware/qca/` |

**Notes**: Identical to mayfly. Requires MHI/QMI/WLFW bring-up sequence before ath11k attaches. PCIe device is `cnss_pci` on root port `pcie0_rp`.

### Bluetooth (QCA6490)
| File | Purpose | Source |
|------|---------|--------|
| `qca/rampatch_*.bin` | Controller rampatch | `/vendor/firmware/qca/` |
| `qca/nvm_*.bin` | NVM configuration | `/vendor/firmware/qca/` |
| `qca/btfw_*.bin` | BT firmware | `/vendor/firmware/qca/` |

**Notes**: Identical to mayfly. BT over GENI UART (SE). Requires BT_EN GPIO, rampatch + NVM download, in-band sleep protocol.

### Audio (waipio-mtp ADSP)
| File | Purpose | Source |
|------|---------|--------|
| `audio/*` | ADSP audio firmware (multiple .bin/.elf) | `/vendor/firmware/audio/` |

**Notes**: Different from mayfly (which uses AW88261). waipio-mtp is the ADSP on SM8475. Requires AudioReach graph, tertiary TDM sink for speakers.

### Wi-Fi MAC (CRITICAL)
| File | Purpose | Source |
|------|---------|--------|
| `wlan_mac.bin` | 6-byte MAC address | `/persist/qca6490/wlan_mac.bin` |

**Notes**: **REQUIRED**. Without it, ath11k stops with "IT HAS NO ADDRESS". Extract from persist partition.

## Kernel Firmware Loading

The XNU kernel expects firmware at specific paths in the iOS rootfs:
```
/usr/share/firmware/
├── a630_zap.bin
├── a630_gmu.bin
├── a630_hfi.bin
├── ath11k/
│   └── QCA6490/
│       └── hw2.0/
│           ├── board.bin
│           ├── firmware-5.bin
│           └── firmware-6.bin
├── qca/
│   ├── rampatch_*.bin
│   ├── nvm_*.bin
│   └── btfw_*.bin
└── audio/
    └── *.bin
```

These must be copied into the iOS rootfs during image build (see `mkiosroot.sh` in ios-sweet).

## Verification

```bash
# Check GPU firmware
ls -la fw-gpu/

# Check Wi-Fi firmware
ls -la fw-wifi/ath11k/QCA6490/hw2.0/

# Check BT firmware
ls -la fw-bt/

# Check Wi-Fi MAC
xxd fw-wifi/wlan_mac.bin
# Should show 6 bytes: XX XX XX XX XX XX
```

## Notes

- Firmware versions must match the Android build on your device
- If you update Android, re-extract firmware
- Some firmware may be signed/encrypted - use the exact blobs from your device
- The kernel driver will fail to load if firmware is missing or mismatched