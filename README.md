# HakiOS on Xiaomi 12T Pro (diting, SM8475)

iOS 16 on Snapdragon 8+ Gen 1 — forked from [HakiOS mayfly](https://github.com/cotunjr/hakios-mayfly) (Xiaomi 12S).

## Status

🚧 **Early bring-up** — adapting mayfly port for diting hardware differences.

### Working (from mayfly, same SoC)
- ✅ SM8475 CPU (8 cores: 4×A510 + 3×A710 + 1×X2)
- ✅ Adreno 730 GPU (Gen 7.4.0, GMU + HFI + zap shader)
- ✅ Display: 1080x2400 120Hz DSC command-mode
- ✅ Wi-Fi: QCA6490 PCIe (ath11k)
- ✅ Bluetooth: QCA6490 UART
- ✅ UFS storage
- ✅ UEFI (Mu-Silicium, blob-free)

### To Adapt (diting-specific)
- 🔄 Touch: Goodix GT9916S on SPI @ 12MHz (vs ST FTS on mayfly)
- 🔄 Buttons: gpio-keys + PMIC PMK8350 pwrkey (vs PMIC arbiter v7)
- 🔄 Audio: waipio-mtp ADSP (vs AW88261)
- 🔄 Panel power: L12-specific sequencing

## Repositories

| Repo | Purpose |
|------|---------|
| `hakios-diting` (this) | Device tree, ADT, build scripts, docs |
| `hakios-xnu-kernel` (fork) | XNU kernel with SM8475 support, mayfly-port branch |
| `hakios-uefi` (fork) | Mu-Silicium UEFI, ditingPkg |
| `hakios-loader` (fork) | xnuloader |

## Quick Start

### Prerequisites
- Linux build machine with `aarch64-linux-gnu-gcc`, `mkbootimg`, `apfs-fuse`, `hfsprogs`
- macOS with Xcode + Docker for kernel CI (GitHub Actions)
- Unlocked bootloader on device
- iPhone X iOS 16.5 (20F66) IPSW from Apple

### Build

```bash
# 1. Fork hakios-xnu-kernel to your GitHub, enable Actions
# 2. Build kernel via CI:
gh workflow run xnu.yml -R YOUR/hakios-xnu-kernel -f target=diting
gh run download RUN_ID -R YOUR/hakios-xnu-kernel -n xnu-kernel -D xnu/out

# 3. Build ADT
cd hakios-diting
python3 tools/mkadt.py out/diting.adt --highmem

# 4. Build boot image
./tools/build-image.sh daily "rd=ufsroot0 ufsrw=1 rootrw=1 cpus=7 launchd_unsecure_cache=1 wdt=-1 ditingfb_noconsole=1 ditingfb_hz=30 ditingusb=2 adsp=1 sound=4 sound_sd=2 sound_below=80 sound_gain=0 speaker_sr=8 qcabt=6 wifi_pcie=12 wifi_lx=2 wifi_station=1 wifi_read_ms=0 wifi_wait_ms=10000 wifi_mac=<YOUR_MAC> fb_hud=1 cpu_mhz=2400"

# 5. Boot on device
fastboot boot out/shim-boot-daily.img
```

### Firmware Extraction (from your device)

```bash
# GPU
adb pull /vendor/firmware/a630_* fw-gpu/
adb pull /vendor/firmware/adreno_* fw-gpu/

# Wi-Fi/BT (QCA6490)
adb pull /vendor/firmware/ath11k/ fw-wifi/
adb pull /vendor/firmware/qca/ fw-wifi/

# Audio
adb pull /vendor/firmware/audio/ fw-audio/

# BT
adb pull /vendor/firmware/qca/ fw-bt/

# Wi-Fi MAC from persist partition
adb pull /dev/block/by-name/persist persist.img
# Extract qca6490/wlan_mac.bin
```

## Hardware Reference

### Device Tree (from Android)
```
Model: Diting based on Qualcomm Technologies, Inc SM8475
Compatible: qcom,cape-mtp qcom,cape qcom,mtp

CPU: 8-core Kryo
  Cluster 0: 4× Cortex-A510 @ 1.8 GHz (MPIDR 0x000-0x300)
  Cluster 1: 3× Cortex-A710 @ 2.75 GHz (MPIDR 0x100-0x300)
  Cluster 2: 1× Cortex-X2 @ 3.19 GHz (MPIDR 0x400)

GPU: Adreno 730 (qcom,adreno-gpu-gen7-4-0)
  Reg: 0x03d00000/0x40000, 0x03d61000/0x800, 0x03d50000/0x1000, 0x03d8b000/0x2000, 0x03d9e000/0x1000, 0x10900000/0x1000
  IRQ: 0x12c, 0x11e

Display: 1080x2400 120Hz DSC
  MDP: qcom,sde-kms @ 0xae00000
  DSI ctrl: 0xae94000, 0xae96000
  DSI phy: 0xae94900, 0xae96900
  Panel: L12 (dsi_panel_pwr_supply_L12)

Touch: Goodix GT9916S (FTS)
  SPI: 0x990000 @ 12MHz
  IRQ: GPIO 60, pin 21, active low
  Reset: GPIO 60, pin 20
  Resolution: 1080x2400

Wi-Fi/BT: QCA6490
  PCIe: 0x1c00000 (pcie0_rp -> cnss_pci)
  BT: bt_qca6490 (GENI UART, PMIC GPIOs)

Audio: waipio-mtp ADSP
  Sound card: waipio-mtp-snd-card

Power: PMIC PMK8350 (SPMI)
  Pwrkey: pmic_pwrkey (PMIC IRQ)
  Buttons: gpio-keys

Memory: 12GB (4GB low @ 0x80000000 + 8GB high @ 0x1_00000000)
Framebuffer: 0xB8000000 (ABL panel memory)
UFS: 0x1d84000
```

## Documentation

- [PORTING_PLAN.md](PORTING_PLAN.md) — Full porting plan and timeline
- [docs/FINDINGS.md](docs/FINDINGS.md) — Hardware findings register-level
- [docs/HISTORY.md](docs/HISTORY.md) — Bring-up timeline
- [docs/BOOT-ARGS.md](docs/BOOT-ARGS.md) — Boot arguments reference
- [docs/FIRMWARE.md](docs/FIRMWARE.md) — Required firmware files
- [docs/OPEN-ISSUES.md](docs/OPEN-ISSUES.md) — Known issues and leads

## References

- [HakiOS mayfly (Xiaomi 12S)](https://github.com/cotunjr/hakios-mayfly) — Base port, same SoC
- [HakiOS XNU kernel](https://github.com/cotunjr/hakios-xnu-kernel) — Kernel source
- [ios-sweet (Redmi Note 10 Pro)](https://github.com/dipa-studio/ios-sweet) — iOS 16.7 reference
- [HackiOS](https://hackiosx.dev/) — Project overview
- [Inside HackiOS](https://singularitymoments.com/content/inside-hackios-booting-apples-xnu-kernel-and-springboard-on-snapdragon-silicon/) — Technical deep dive

## License

Research/educational. No Apple binaries or proprietary firmware in this repo.
Firmware blobs must be extracted from your own device.
IPSW must be downloaded from Apple.