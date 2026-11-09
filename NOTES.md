# iOS 16 on diting (Xiaomi 12T Pro, SM8475) - working notes

## Agent handoff / active work (2026-11-09)

### STATE at 2026-11-09 (initial bring-up)

**Device**: Xiaomi 12T Pro (22081212UG), codename `diting`, SM8475 (Snapdragon 8+ Gen 1)
**Bootloader**: Unlocked (orange state confirmed)
**Android**: 16 (AQ3A.250226.002/OS3.0.4.0.VLFMIXM)

**Hardware collected from live device tree:**
- CPU: 8-core Kryo (4×A510 @1.8GHz, 3×A710 @2.75GHz, 1×X2 @3.19GHz)
- GPU: Adreno 730 (Gen 7.4.0) - SAME as mayfly
- Display: 1080x2400 120Hz DSC, MDP @0xae00000, DSI ctrl @0xae94000/0xae96000
- Touch: Goodix GT9916S on SPI @0x990000 12MHz, IRQ GPIO60 pin21, Reset GPIO60 pin20
- Wi-Fi/BT: QCA6490 on PCIe @0x1c00000 (cnss_pci) - SAME as mayfly
- Audio: waipio-mtp ADSP
- Buttons: gpio-keys + PMIC PMK8350 pwrkey
- Memory: 12GB (4GB low @0x80000000 + 8GB high @0x1_00000000)
- Framebuffer: 0xB8000000 (ABL panel memory)
- UFS: @0x1d84000
- GICv3: 0x17a00000/0x17a60000

**Reference port**: HakiOS mayfly (Xiaomi 12S, same SM8475 SoC) - WORKING iOS 16.5
- Repo: https://github.com/cotunjr/hakios-mayfly
- Kernel: https://github.com/cotunjr/hakios-xnu-kernel (branch mayfly-port)

**Created so far:**
- `hakios-diting/` device repository structure
- `tools/mkadt.py` - ADT builder for diting (based on mayfly + ios-sweet) ✓ WORKING
- `configs/diting_defconfig` - XNU kernel config
- `tools/build-image.sh` - Boot image builder
- `tools/run.sh` - Device boot and log collection
- `tools/diting-log-pull.sh` - Kernel log extraction from userdata
- `README.md`, `AGENTS.md`, `PORTING_PLAN.md`
- `../hakios-xnu-kernel/devices/diting/` - Device repository in kernel tree:
  - `device.conf` - Device metadata
  - `soc/soc.conf` - SM8475 SoC definition
  - `soc/configs/sm8475.config` - SoC fragment
  - `configs/diting_defconfig` - Kernel defconfig (includes common + sm8475 + diting)
  - `configs/diting.config` - Device fragment (drivers enabled)
  - `drivers/input/conf` + `hakios.diting_touch.c` - Goodix GT9916S SPI touch driver stub
  - `drivers/input/hakios.diting_keys.c` - gpio-keys + PMIC PMK8350 pwrkey driver stub
  - `drivers/audio/conf` + `hakios.diting_audio.c` - waipio-mtp ADSP audio driver stub
  - `soc/hakios.diting.c` - SoC-specific init stub
  - `drivers/wifi/conf` + `hakios.diting_qca6490.c` - QCA6490 Wi-Fi driver (full impl from mayfly)
- `../hakios-xnu-kernel/xnu/files/pexpert/arm64/SM8475.h` - Board config header
- `../hakios-xnu-kernel/xnu/hakios.patch` - XNU patch with SM8475 machine flags
- `../hakios-xnu-kernel/.github/workflows/build-kernel.yml` - GitHub Actions CI workflow

**Next actions (in order):**
1. **Fork `hakios-xnu-kernel` to GitHub, enable Actions, build diting kernel** ← CURRENT
2. Test ADT generation: `python3 tools/mkadt.py out/diting.adt --highmem --dump` ✓ DONE
3. Create kernel driver stubs for diting-specific hardware ✓ DONE (stubs created)
4. Build UEFI (ditingPkg in Mu-Silicium)
5. Build xnuloader
6. Extract firmware blobs from device
7. Download iPhone X iOS 16.5 (20F66) IPSW
8. Build iOS rootfs for userdata
9. Integration test: fastboot boot shim image

**Blockers:**
- Need GitHub fork of hakios-xnu-kernel for CI kernel builds
- Need macOS machine for kernel CI (GitHub Actions provides free macOS runners)
- Firmware blobs not yet extracted from device
- Need to implement driver logic (currently stubs only for touch, buttons, audio, SoC init)
- Need to verify register addresses from live device tree

### 2026-11-09: Device Repository Created
- Cloned hakios-xnu-kernel (mayfly-port branch)
- Created `devices/diting/` with device.conf, soc/, configs/, drivers/
- Added driver stubs: GT9916S touch, DITING_KEYS buttons, WAIPU_MTP audio
- Added SoC init stub for SM8475
- ADT generation tested and working (--dump shows valid tree)

**Artifacts on disk:**
- `ios-port-diting/boot.img` - Android boot image (192MB)
- `ios-port-diting/dtbo.img` - DTBO (25MB)
- `ios-port-diting/vendor_boot.img` - Vendor boot (100MB)
- `ios-port-diting/ios-sweet/` - Reference ios-sweet repo
- `ios-port-diting/hakios-diting/` - New device repo

### Hardware Findings (register-level)

#### Touch (Goodix GT9916S)
```
SPI: 0x990000 (spi@990000)
Compatible: st,spigoodix,gt9916S
Reg: <0>
SPI max frequency: 12000000 (12 MHz)
IRQ GPIO: <&gpio 60 21 8> (GPIO controller phandle 0x3c, pin 21, active low)
Reset GPIO: <&gpio 60 20 0> (GPIO controller phandle 0x3c, pin 20)
Interrupts: <21 8> (IRQ 21, active low)
X-max: 1080
Y-max: 2400
```
Linux driver: `drivers/input/touchscreen/goodix_gt9916s.c`

#### Buttons
```
gpio-keys:
  power: KEY_POWER (116), wakeup
  volume_up: KEY_VOLUMEUP (115)
  volume_down: KEY_VOLUMEDOWN (114)

pmic_pwrkey (PMK8350):
  PMIC IRQ via SPMI
  Compatible: qcom,pmk8350-pwrkey
```

#### Display
```
Panel: L12 (dsi_panel_pwr_supply_L12)
MDP: qcom,sde-kms @ 0xae00000
DSI ctrl0: 0xae94000
DSI ctrl1: 0xae96000
DSI phy0: 0xae94900
DSI phy1: 0xae96900
Canvas: 1125x2436 (iPhone X 3x scale)
Framebuffer: 0xB8000000 (1080x2400, stride 4320)
```

#### GPU (Adreno 730) - SAME as mayfly
```
Compatible: qcom,adreno-gpu-gen7-4-0 qcom,kgsl-3d0
Reg: 
  0x03d00000/0x40000 (GPU core)
  0x03d61000/0x800
  0x03d50000/0x1000
  0x03d8b000/0x2000
  0x03d9e000/0x1000
  0x10900000/0x1000
Interrupts: 0x12c, 0x11e (GIC SPI)
Features: GMU, HFI, zap shader auth by TZ
```

#### Wi-Fi/BT (QCA6490) - SAME as mayfly
```
PCIe: 0x1c00000 (pcie@1c00000)
  Root port: pcie0_rp
    cnss_pci: compatible qcom,cnss-pci
BT: bt_qca6490 (qcom,qca6490)
  Mboxes, GPIOs for reset/sw_ctrl/vdd supplies
  UART on GENI SE
```

#### CPU Topology
```
Cluster 0 (efficiency): 4× Cortex-A510
  MPIDR: 0x000, 0x100, 0x200, 0x300
  Freq: 1.8 GHz

Cluster 1 (performance): 3× Cortex-A710
  MPIDR: 0x100, 0x200, 0x300 (cluster 1)
  Freq: 2.75 GHz

Cluster 2 (prime): 1× Cortex-X2
  MPIDR: 0x400 (cluster 2)
  Freq: 3.19 GHz
```

#### Memory Map
```
Low bank:  0x80000000 - 0x1_00000000 (4GB)
High bank: 0x1_00000000 - 0x3_00000000 (8GB)
Total: 12GB

Kernel RAM: 0x80000000 + 4GB (minus panic log)
Framebuffer: 0xB8000000 (in low bank)
UFS: 0x1d84000
GICD: 0x17a00000
GICR: 0x17a60000
```

### Boot Arguments (planned)
```
rd=ufsroot0 ufsrw=1 rootrw=1
cpus=7
launchd_unsecure_cache=1
wdt=-1
ditingfb_noconsole=1
ditingfb_hz=30
ditingusb=2
adsp=1
sound=4
sound_sd=2
sound_below=80
sound_gain=0
speaker_sr=8
qcabt=6
wifi_pcie=12
wifi_lx=2
wifi_station=1
wifi_read_ms=0
wifi_wait_ms=10000
wifi_mac=<FROM_PERSIST>
fb_hud=1
cpu_mhz=2400
```

### Firmware Needed (extract from device)
```
fw-gpu/
  a630_zap.*       # Zap shader
  a630_gmu.*       # GMU firmware
  a630_hfi.*       # HFI firmware
  adreno_*         # Adreno blobs

fw-wifi/
  ath11k/          # ath11k firmware (QCA6490)
  qca/             # QCA blobs

fw-audio/
  audio/           # ADSP audio firmware

fw-bt/
  qca/             # BT rampatch + NVM

persist/
  qca6490/wlan_mac.bin  # Wi-Fi MAC (REQUIRED for ath11k)
```

### iOS Rootfs
- iPhone X iOS 16.5 (20F66) IPSW from Apple
- OR iOS 16.7.16 (20H392) like ios-sweet
- Extract: rootfs.dmg, SystemOS.dmg, AppOS.dmg, cryptexes
- Build APFS image for userdata (16GB+)

### Commands Run
```bash
# Device info
adb -s 5cb98ef7 shell getprop ro.product.model        # 22081212UG
adb -s 5cb98ef7 shell getprop ro.product.device       # diting
adb -s 5cb98ef7 shell getprop ro.boot.flash.locked    # orange (unlocked)

# Partitions pulled
adb shell 'cat /dev/block/by-name/boot_a' > boot.img
adb shell 'cat /dev/block/by-name/dtbo_a' > dtbo.img
adb shell 'cat /dev/block/by-name/vendor_boot_a' > vendor_boot.img

# Device tree explored via /sys/firmware/devicetree/base/
```

### Validation Results (2026-11-09)
```
$ python3 tools/mkadt.py out/diting.adt --highmem --dump
# Produces valid 13KB ADT with all nodes: chosen, cpus, arm-io, gpu, ufs, pcie0, spi0, spmi, adsp, fbcon, buttons, pram

$ python3 tools/hakios-config.py defconfig devices/diting/configs/diting_defconfig
# .config made from defconfig, common_defconfig, sm8475.config, diting.config, diting_defconfig
# 47 characters of boot-arguments; kernel.ver=2.1.13-hakios-darwin22.5-sm8475-g9d3c291a-dirty

$ python3 tools/hakios-config.py check
# .config: 41 symbols set, 47 characters of boot-arguments (the kernel holds 607; a run adds about 260)

$ python3 tools/drivers-check.py
# drivers-check: 49 files in 12 subsystems, all listed, all present, each built by one drivers/*/conf block

$ python3 tools/hakios-config.py show
# drivers built in: adsp speaker sound virtio_sound bt gpu adreno virtio_input goodix buttons qmi virtio_net battery ufs virtio_blk wifi_stack waipu_mtp diting_sound gt9916s diting_keys qca6490
# drivers left out: mic camera torch socinfo haptic modem cpufreq thermal pmic battguard wifi
# boot-arguments: cpus=1 ufs=2 touchscreen=1 gpu=1 adsp=1 sound=4
```