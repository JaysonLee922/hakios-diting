# Open Issues - diting (Xiaomi 12T Pro)

## Critical (Blockers)

### 1. Kernel CI Setup
**Status**: Not started
**Issue**: Need to fork `hakios-xnu-kernel` to GitHub and enable Actions for macOS kernel builds.
**Lead**: Fork repo, add `diting_defconfig`, trigger `xnu.yml` workflow.

### 2. Firmware Extraction
**Status**: Not started
**Issue**: All firmware blobs must be extracted from the device before integration testing.
**Lead**: Run extraction commands in `FIRMWARE.md`.

### 3. IPSW Download
**Status**: Not started
**Issue**: Need iPhone X iOS 16.5 (20F66) or 16.7.16 (20H392) IPSW from Apple.
**Lead**: Download from Apple's signing server (while still signed) or archive.org.

---

## High Priority

### 4. Touch Driver (Goodix GT9916S)
**Status**: Not started
**Issue**: Mayfly uses ST FingerTip (FTS) on SPI. Diting uses Goodix GT9916S on SPI @ 12MHz.
**Differences**:
- Different register map
- Different interrupt handling (active low IRQ)
- Different firmware loading
- FOD (fingerprint on display) support
**Lead**: Port Linux `drivers/input/touchscreen/goodix_gt9916s.c` to XNU as `hakios.diting_touch.c`.
**Reference**: ios-sweet `bsd/dev/sweet_touch.c`, mayfly `drivers/input/hakios.stfts.c`.

### 5. Buttons Driver (gpio-keys + PMIC pwrkey)
**Status**: Not started
**Issue**: Mayfly uses PMIC arbiter v7. Diting uses gpio-keys + PMIC PMK8350 pwrkey.
**Differences**:
- Power key via PMIC SPMI interrupt (not GPIO)
- Volume keys via gpio-keys
- Different wakeup handling
**Lead**: Create `hakios.diting_keys.c` combining gpio-keys and PMIC pwrkey.
**Reference**: Linux `drivers/input/keyboard/gpio_keys.c`, `drivers/input/misc/qcom-pmk8350-pwrkey.c`.

### 6. Audio Driver (waipio-mtp ADSP)
**Status**: Not started
**Issue**: Mayfly uses AW88261 speakers via ADSP. Diting uses waipio-mtp ADSP with different audio graph.
**Differences**:
- Different ADSP firmware
- Different speaker amp (no AW88261)
- Different TDM configuration
- Headset jack detection different
**Lead**: Create `hakios.diting_audio.c` based on mayfly audio section.
**Reference**: Linux `sound/soc/qcom/waipio*.c`.

### 7. Panel Power Sequencing (L12)
**Status**: Not started
**Issue**: Mayfly panel timing may not match diting's L12 panel.
**Differences**:
- Different power supply sequencing (dsi_panel_pwr_supply_L12)
- Different DSC configuration
- Different TE (tear effect) GPIO
**Lead**: Verify ADT display timing matches Android panel driver.
**Reference**: Android `drivers/gpu/drm/msm/dsi/panel/`.

---

## Medium Priority

### 8. Prime Core (Cortex-X2) Handling
**Status**: Not started
**Issue**: Diting has 1× Cortex-X2 @ 3.19 GHz (cluster 2). Mayfly has 2× Cortex-A78 @ 2.4 GHz.
**Concerns**:
- Different microarchitecture (X2 vs A78)
- Higher power/thermal
- May need separate frequency/voltage scaling
- `cpus=7` enables it, but may cause instability
**Lead**: Test with `cpus=6` first (disable prime core), then enable with thermal monitoring.

### 9. Thermal Management
**Status**: Not started
**Issue**: SM8475 runs hot. Mayfly hits 86-94°C thermal reset under load.
**Concerns**:
- Diting has same SoC but different thermal solution
- TSENS readings needed
- Thermal governor must step down frequencies
**Lead**: Implement thermal driver reading TSENS, integrate with CPU cooling.

### 10. Battery / Charging
**Status**: Not started
**Issue**: Mayfly shows battery level via ADSP but no charge control. Diting uses PMK8350 charger.
**Concerns**:
- Different PMIC (PMK8350 vs PM6150L)
- Charging not implemented in either port
- Battery health page spins
**Lead**: Add PMK8350 charger driver, expose via IOPMPowerSource.

### 11. USB Host Mode
**Status**: Not started
**Issue**: Only USB device mode (fastboot/CDC-ECM) works. No USB host in iOS.
**Concerns**:
- DWC3 host controller not initialized
- No USB accessory support
- No ADB over USB in iOS
**Lead**: Implement DWC3 host mode in xnuloader/XNU.

---

## Low Priority / Research

### 12. Camera
**Status**: Not started
**Issue**: No camera support in any port yet.
**Lead**: Requires CAMSS/IFE/CSID drivers, ISP firmware, sensor drivers.

### 13. Cellular / Modem
**Status**: Not started
**Issue**: Modem firmware separate, QRTR/QMI interface needed.
**Lead**: Requires modem bring-up, RIL daemon, SIM support.

### 14. Sensors (Accel, Gyro, Proximity, ALS)
**Status**: Not started
**Issue**: Sensor hub on SPMI/I2C, need IIO drivers.
**Lead**: Port Linux sensor drivers.

### 15. Haptics
**Status**: Not started
**Issue**: PMIC HV haptics via SPMI.
**Lead**: Port `qcom-hv-haptics` driver.

### 16. Secure Enclave / SEP
**Status**: Not started
**Issue**: No SEP on Snapdragon. Touch ID / Face ID won't work.
**Lead**: Stub or emulate for iOS compatibility.

### 17. App Store / Apple ID / iCloud
**Status**: Not started
**Issue**: Requires valid device certificates, FairPlay, provisioning.
**Lead**: Research activation bypass (mobileactivationd Hactivation branch).

---

## Resolved / Not Applicable

### GPU Driver
**Status**: RESOLVED (inherited from mayfly)
**Details**: Adreno 730 driver works identically on SM8475.

### Wi-Fi / BT Driver
**Status**: RESOLVED (inherited from mayfly)
**Details**: QCA6490 on PCIe identical to mayfly.

### Display Driver
**Status**: RESOLVED (inherited from mayfly)
**Details**: MDP/SDE KMS + DSI command mode identical. Only panel timing differs.

### UFS Storage
**Status**: RESOLVED (inherited from mayfly)
**Details**: UFS host controller identical.

### UEFI / Loader
**Status**: RESOLVED (inherited from mayfly)
**Details**: Mu-Silicium + xnuloader work on SM8475. Need ditingPkg.

### iOS Rootfs
**Status**: RESOLVED (process known from ios-sweet/mayfly)
**Details**: Same iPhone X IPSW, same APFS build process.

---

## Testing Checklist

When each component is implemented, verify:

- [ ] Kernel compiles with diting_defconfig
- [ ] ADT generates without errors (`--dump` shows correct tree)
- [ ] QEMU boots to XNU console (with `--qemu` ADT)
- [ ] Fastboot boot works on device
- [ ] Kernel console visible (serial/USB)
- [ ] Persistent log captures boot output
- [ ] USB networking works (`ditingusb=2`)
- [ ] Touch input reaches IOHID (backboardd)
- [ ] Buttons reach IOHID (power/volume)
- [ ] Display shows Apple logo / progress
- [ ] GPU initializes (Metal/freedreno)
- [ ] Wi-Fi scans / connects
- [ ] Bluetooth pairs
- [ ] Audio plays (speakers)
- [ ] SpringBoard home screen visible
- [ ] Thermal throttling works
- [ ] Battery level shown
- [ ] Sleep/wake works

---

## Debugging Resources

### Log Collection
```bash
# Live USB network log (ditingusb=2)
nc -ul 5140 > logs/live.txt

# Recovery mode log pull
fastboot boot recovery/recovery.img
./tools/diting-log-pull.sh logs/boot.txt
adb reboot bootloader
```

### Kernel Debug Flags
```
debug=0xc serial=3 keepsyms=1 -enable_kprintf_spam -noprogress
```

### Boot Arg for Debugging
```
ditingfb_noconsole=0  # Show kernel text over GUI (see panics)
cpus=1                # Single core for debugging
fb_hud=1              # Show FPS
```

### Useful ADB Commands (Android)
```bash
# Check device tree
adb shell 'cat /sys/firmware/devicetree/base/soc/...'

# Check interrupts
adb shell 'cat /proc/interrupts | grep -iE "gpu|touch|spi|pcie"'

# Check clocks
adb shell 'cat /sys/kernel/debug/clk/clk_summary'

# Check thermal
adb shell 'cat /sys/class/thermal/thermal_zone*/temp'
```

### QEMU Smoke Test
```bash
cd hakios-xnu-kernel
python3 tools/mkadt.py qemu.adt --qemu
python3 tools/qemu-sweet.py --secs 30 --kernel xnu/out/kernel.development.diting --adt qemu.adt --ramdisk root-fork.img
```