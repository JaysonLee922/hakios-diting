# Bring-up History - Xiaomi 12T Pro (diting)

## 2026-11-09: Initial Reconnaissance
- Device connected via ADB (serial: 5cb98ef7)
- Confirmed: Xiaomi 12T Pro (22081212UG), codename `diting`, SM8475
- Bootloader unlocked (orange state)
- Android 16 (AQ3A.250226.002/OS3.0.4.0.VLFMIXM)
- Pulled partitions: boot_a (192MB), dtbo_a (25MB), vendor_boot_a (100MB)
- Explored live device tree via `/sys/firmware/devicetree/base/`
- Identified all major hardware components
- Confirmed SoC/GPU/Display/Wi-Fi/BT identical to working mayfly port
- Created `hakios-diting` device repository with:
  - ADT builder (mkadt.py)
  - Kernel config (diting_defconfig)
  - Build scripts (build-image.sh, run.sh, diting-log-pull.sh)
  - Documentation (README, PORTING_PLAN, FINDINGS, AGENTS, NOTES)

## Next Milestones

### Week 1: Repository & Kernel Setup
- [ ] Fork hakios-xnu-kernel to GitHub
- [ ] Enable GitHub Actions (macOS runners)
- [ ] Add diting_defconfig to kernel
- [ ] Build kernel via CI
- [ ] Test ADT generation

### Week 2: Device Tree & Drivers
- [ ] Validate ADT with --dump
- [ ] Create touch driver stub (Goodix GT9916S)
- [ ] Create buttons driver stub (gpio-keys + PMIC)
- [ ] Create audio driver stub (waipio-mtp)
- [ ] Create SoC init (diting.c)

### Week 3: UEFI & Loader
- [ ] Create ditingPkg in Mu-Silicium
- [ ] Build UEFI firmware
- [ ] Build xnuloader

### Week 4: Firmware & Rootfs
- [ ] Extract firmware blobs from device
- [ ] Download iPhone X iOS 16.5 IPSW
- [ ] Build iOS rootfs for userdata

### Week 5-6: Integration
- [ ] Build complete boot image
- [ ] Test fastboot boot on device
- [ ] Debug via USB networking
- [ ] Iterate to SpringBoard home screen