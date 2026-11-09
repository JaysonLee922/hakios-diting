# iOS 16 on Xiaomi 12T Pro (diting) - Porting Plan

## Project Overview
Port iOS 16 (Darwin userland 16.5/16.7) to Xiaomi 12T Pro (codename "diting", SM8475/Snapdragon 8+ Gen 1) using HakiOS/mayfly architecture:
- **Boot chain**: UEFI (Mu-Silicium) → xnuloader → XNU + Darwin ramdisk → iOS userland
- **Boot method**: `fastboot boot` (RAM-only, preserves Android)
- **iOS rootfs**: userdata partition (APFS/HFS+)
- **Reference**: hackiosx.dev (HakiOS) and ios-sweet (Redmi Note 10 Pro/SM7150)

## Hardware Specifications
| Component | Specification |
|-----------|--------------|
| SoC | SM8475 (Snapdragon 8+ Gen 1) |
| CPU | 1× Cortex-X2 (prime, 3.19 GHz) + 3× Cortex-A710 (performance, 2.75 GHz) + 4× Cortex-A510 (efficiency, 1.8 GHz) |
| GPU | Adreno 730 (Gen 7.4.0) |
| RAM | 12GB LPDDR5 (4GB low @ 0x80000000 + 8GB high @ 0x1_00000000) |
| Display | 1080×2400 120Hz DSC, MDP @ 0xae00000, DSI @ 0xae94000/0xae96000 |
| Touch | Goodix GT9916S on SPI @ 0x990000 (12 MHz), IRQ GPIO60 pin21 |
| Wi-Fi/BT | QCA6490 on PCIe @ 0x1c00000 |
| Audio | waipio-mtp ADSP |
| Buttons | gpio-keys + PMIC PMK8350 pwrkey |
| Storage | UFS @ 0x1d84000 |
| Framebuffer | 0xB8000000 (ABL panel memory, 1080×2400 stride 4320) |
| GICv3 | Distributor 0x17a00000, Redistributor 0x17a60000 |

## Phase 1: Kernel & Build Infrastructure ✓ COMPLETED

### 1.1 Device Repository Structure ✓
- `hakios-diting/` - Main device repository
- `hakios-xnu-kernel/devices/diting/` - Device repo in kernel tree

### 1.2 ADT Builder ✓
- `tools/mkadt.py` - Builds Apple Device Tree for diting
- Tested with `--highmem --dump` - produces valid 13KB ADT

### 1.3 Kernel Configuration ✓
- `configs/diting_defconfig` - Main defconfig (includes common + sm8475 + diting)
- `devices/diting/configs/diting.config` - Device fragment with drivers enabled
- `devices/diting/soc/configs/sm8475.config` - SoC fragment
- Validation: `hakios-config.py check` passes (41 symbols, 47 chars boot args)

### 1.4 Driver Stubs Created ✓
| Driver | File | Status |
|--------|------|--------|
| Touch (GT9916S) | `drivers/input/hakios.diting_touch.c` | Stub |
| Buttons (gpio-keys + PMK8350) | `drivers/input/hakios.diting_keys.c` | Stub |
| Audio (waipio-mtp) | `drivers/audio/hakios.diting_audio.c` | Stub |
| SoC init | `soc/hakios.diting.c` | Stub |
| Wi-Fi (QCA6490) | `drivers/wifi/hakios.diting_qca6490.c` | Full implementation (adapted from mayfly) |

### 1.5 XNU Patch ✓
- `xnu/files/pexpert/arm64/SM8475.h` - Board config header
- `xnu/hakios.patch` - Includes SM8475 machine flags (MAX_CPUS=8, MAX_CPU_CLUSTERS=3, -mcpu=cortex-a710)

### 1.6 GitHub Actions Workflow ✓
- `.github/workflows/build-kernel.yml` - Builds kernel on macOS-14 runners
- Supports manual dispatch with device selection (diting, redwood, qemu)

---

## Phase 2: Kernel Build & CI ⬜ IN PROGRESS

### 2.1 Fork & Enable CI
- [ ] Fork `hakios-xnu-kernel` to GitHub (user's account)
- [ ] Enable GitHub Actions on fork
- [ ] Push current branch (mayfly-port with diting changes)
- [ ] Run workflow_dispatch for `diting` device
- [ ] Verify kernel builds successfully (~8 min on macOS)

### 2.2 Verify Build Artifacts
- [ ] Download `kernel` artifact from CI
- [ ] Verify kernel binary: `file hakios-kernel` shows Mach-O 64-bit arm64
- [ ] Verify version string includes `sm8475`

---

## Phase 3: Boot Components ⬜ PENDING

### 3.1 UEFI (ditingPkg in Mu-Silicium)
- [ ] Fork/clone `hakios-uefi` repository
- [ ] Create `ditingPkg/` based on mayfly's UEFI platform
- [ ] Configure for SM8475: GICv3, PSCI, UART @ 0x0a880000
- [ ] Build UEFI firmware (EDK2)
- [ ] Test in QEMU with `-bios` option

### 3.2 xnuloader
- [ ] Build loader: `make loader` (requires IPSW for identity)
- [ ] Or build placeholder: `PLACEHOLDER=1 make loader-open`
- [ ] Verify `xnuloader/loader.efi` produced

### 3.3 Firmware Extraction
- [ ] Run `devices/diting/pull-firmware.sh` on connected device
- [ ] Verify all firmware directories populated:
  - `fw-gpu/` - Adreno 730 (a630_gmu.bin, a630_zap.fw, etc.)
  - `fw-wifi/` - QCA6490 (ath11k/, qca/)
  - `fw-audio/` - waipio-mtp ADSP
  - `fw-bt/` - QCA6490 BT rampatch/nvm
  - `fw-wifi/qca6490/wlan_mac.bin` - Wi-Fi MAC from persist

---

## Phase 4: iOS Userland ⬜ PENDING

### 4.1 IPSW Download
- [ ] Download iPhone X (iPhone10,3/D22AP) iOS 16.5 (20F66) IPSW from Apple
- [ ] OR iOS 16.7.16 (20H392) like ios-sweet uses
- [ ] Verify SHA256 matches known good

### 4.2 Rootfs Build
- [ ] `make unpack IPSW=/path/to/ipsw` - Extract Darwin userland to `sysimage/`
- [ ] `make images` - Build `userland/root.apfs` and `userland/system.apfs`
- [ ] Verify APFS images mountable

### 4.3 Userdata Partition
- [ ] Flash rootfs to userdata partition (preserves Android)
- [ ] Or build combined boot image with rootfs in ramdisk

---

## Phase 5: Integration & Testing ⬜ PENDING

### 5.1 Boot Image Assembly
- [ ] `./tools/build-image.sh daily "boot args..."` in hakios-diting
- [ ] Generates `out/shim-boot-daily.img`
- [ ] Components: kernel + ADT + cmdline + xnuloader shim

### 5.2 Device Boot Test
- [ ] Put device in fastboot mode: `adb reboot bootloader`
- [ ] `fastboot boot out/shim-boot-daily.img`
- [ ] Observe: UEFI → xnuloader → XNU → Darwin → iOS

### 5.3 Log Collection
- [ ] USB networking: `ditingusb=2` → CDC-ECM at 192.168.7.2
- [ ] `nc -ul 5140 > logs/live.txt`
- [ ] Or recovery mode: `fastboot boot recovery/recovery.img` → `./tools/diting-log-pull.sh`

### 5.4 Driver Bring-up Order
1. **Framebuffer/Display** - Verify GUI appears
2. **Touch (GT9916S)** - Implement SPI communication
3. **Buttons (gpio-keys + PMK8350)** - Implement SPMI/IRQ handling
4. **GPU (Adreno 730)** - Verify Mesa rendering
5. **Audio (waipio-mtp)** - ADSP bring-up
6. **Wi-Fi (QCA6490)** - WLFW/QMI sequence + ath11k
7. **Bluetooth** - QCA6490 BT side
8. **Cellular** - Modem (optional, lower priority)

---

## Phase 6: Driver Implementation Details ⬜ PENDING

### 6.1 Touch Driver (GT9916S)
- Reference: Linux `drivers/input/touchscreen/goodix_gt9916s.c`
- SPI: 12 MHz, mode 0, 8-bit
- IRQ: GPIO60 pin21 (active low)
- Reset: GPIO60 pin20
- Register map: 0x8047 (product ID), 0x8048 (config version), 0x814E (coord addr)
- I2C-style register access over SPI

### 6.2 Buttons Driver
- gpio-keys: power (KEY_POWER), vol_up (KEY_VOLUMEUP), vol_down (KEY_VOLUMEDOWN)
- PMK8350 pwrkey: SPMI interrupt, compatible `qcom,pmk8350-pwrkey`
- Reference: `hakios.buttons.c` + mayfly's implementation

### 6.3 Audio Driver (waipio-mtp)
- ADSP: Q6 DSP with AudioReach framework
- Reference: `hakios.adsp.c`, `hakios.audio.c`, `hakios.sound.c`
- Requires: ADSP firmware from `fw-audio/audio/`
- Speaker guard: `hakios.guard.c` (copied from common)

### 6.4 GPU Driver (Adreno 730)
- Already working in mayfly (same GPU)
- Steps: GMU init → HFI → GX → GMU FW → GPU FW → zap shader
- Reference: `hakios.adreno.c` + mayfly's adreno7.c

### 6.5 Wi-Fi Driver (QCA6490)
- Already implemented in `hakios.diting_qca6490.c` (adapted from mayfly)
- WLFW service over QMI/QRTR on MHI/PCIe
- ath11k Linux driver integration (`CONFIG_HAKIOS_WIFI_STACK=y`)
- Requires: `fw-wifi/ath11k/QCA6490/hw2.0/` firmware

---

## Boot Arguments Reference

```bash
# Core
rd=ufsroot0 ufsrw=1 rootrw=1
cpus=7                          # Use all 8 cores (0-7)
launchd_unsecure_cache=1
wdt=-1                          # Disable watchdog

# Display
ditingfb_noconsole=1            # Hide kernel text over GUI
ditingfb_hz=30                  # Frame rate
fb_hud=1                        # FPS counter

# USB
ditingusb=2                     # CDC-ECM at 192.168.7.2

# Audio
adsp=1
sound=4
sound_sd=2
sound_below=80
sound_gain=0
speaker_sr=8

# Bluetooth
qcabt=6

# Wi-Fi
wifi_pcie=12                    # PCIe link + MHI + QRTR
wifi_lx=2                       # ath11k driver
wifi_station=1
wifi_read_ms=0
wifi_wait_ms=10000
wifi_mac=<FROM_PERSIST>         # MAC from persist partition

# CPU
cpu_mhz=2400
```

---

## Key Files Reference

| Component | Path |
|-----------|------|
| ADT Builder | `hakios-diting/tools/mkadt.py` |
| Kernel Defconfig | `hakios-diting/configs/diting_defconfig` |
| Device Fragment | `hakios-xnu-kernel/devices/diting/configs/diting.config` |
| SoC Fragment | `hakios-xnu-kernel/devices/diting/soc/configs/sm8475.config` |
| Touch Driver | `hakios-xnu-kernel/drivers/input/hakios.diting_touch.c` |
| Buttons Driver | `hakios-xnu-kernel/drivers/input/hakios.diting_keys.c` |
| Audio Driver | `hakios-xnu-kernel/drivers/audio/hakios.diting_audio.c` |
| Wi-Fi Driver | `hakios-xnu-kernel/devices/diting/drivers/wifi/hakios.diting_qca6490.c` |
| SoC Init | `hakios-xnu-kernel/devices/diting/soc/hakios.diting.c` |
| Board Config | `hakios-xnu-kernel/xnu/files/pexpert/arm64/SM8475.h` |
| Boot Image Builder | `hakios-diting/tools/build-image.sh` |
| Run Script | `hakios-diting/tools/run.sh` |
| Log Pull | `hakios-diting/tools/diting-log-pull.sh` |
| Firmware Pull | `hakios-xnu-kernel/devices/diting/pull-firmware.sh` |

---

## Progress Tracking

| Date | Milestone | Status |
|------|-----------|--------|
| 2026-11-09 | Device repository created | ✓ |
| 2026-11-09 | ADT generation working | ✓ |
| 2026-11-09 | Kernel config validated | ✓ |
| 2026-11-09 | Driver stubs created | ✓ |
| 2026-11-09 | XNU patch with SM8475 | ✓ |
| 2026-11-09 | GitHub Actions workflow created | ✓ |
| 2026-11-09 | PORTING_PLAN.md created | ✓ |
| - | Fork & CI build | ⬜ |
| - | Firmware extracted | ⬜ |
| - | IPSW downloaded | ⬜ |
| - | UEFI built | ⬜ |
| - | xnuloader built | ⬜ |
| - | Rootfs built | ⬜ |
| - | First boot attempt | ⬜ |

---

## Next Immediate Action

**Fork `hakios-xnu-kernel` to GitHub and run the CI build for diting:**

```bash
# On GitHub: fork cotunjr/hakios-xnu-kernel to your account
# Clone your fork locally
git remote add myfork https://github.com/YOUR_USERNAME/hakios-xnu-kernel.git
git push myfork mayfly-port:diting-port

# Enable Actions on your fork, then trigger workflow_dispatch for "diting"
# Or push to trigger: git push myfork diting-port
```

Once the kernel builds successfully on CI, download the artifact and proceed with UEFI, xnuloader, and firmware extraction.