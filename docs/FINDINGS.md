# Hardware Findings - Xiaomi 12T Pro (diting, SM8475)

Register-level facts collected from live Android device tree (`/sys/firmware/devicetree/base/`) and `dmesg`.

## SoC
- **Model**: Qualcomm SM8475 (Snapdragon 8+ Gen 1)
- **Compatible**: `qcom,cape-mtp` `qcom,cape` `qcom,mtp`
- **CPU**: 8-core Kryo (ARMv8)
  - Cluster 0: 4× Cortex-A510 @ 1.8 GHz (MPIDR 0x000-0x300)
  - Cluster 1: 3× Cortex-A710 @ 2.75 GHz (MPIDR 0x100-0x300, cluster 1)
  - Cluster 2: 1× Cortex-X2 @ 3.19 GHz (MPIDR 0x400, cluster 2)
- **PSCI**: `psci` enable-method
- **Timebase**: 19.2 MHz
- **Virtual timer**: INTID 19 (PPI)

## Memory
- **Low bank**: 0x80000000 - 0x1_00000000 (4 GiB)
- **High bank**: 0x1_00000000 - 0x3_00000000 (8 GiB)
- **Total**: 12 GiB LPDDR5
- **Reserved regions**: Multiple carve-outs in low bank (XPU, TZ, modem, etc.)

## GICv3
- **GICD**: 0x17a00000 (size 0x10000)
- **GICR**: 0x17a60000 (size 0x100000)
- **ITS**: Present at 0x17a80000 (inferred)
- **Virtual timer**: PPI 19

## Display
- **MDP (MSM Display Processor)**: `qcom,sde-kms` @ 0xae00000
- **DSI Controller 0**: 0xae94000
- **DSI Controller 1**: 0xae96000
- **DSI PHY 0**: 0xae94900
- **DSI PHY 1**: 0xae96900
- **DP Display**: 0xae90000 (qcom,dp_display)
- **Primary panel**: `qcom,dsi-display-primary` (label "primary")
  - MDP phandle: 0x4ca
  - DSI ctrl phandles: 0x4ce, 0x4cf
  - DSI phy phandles: 0x4d0, 0x4d1
  - Panel power: L12 (dsi_panel_pwr_supply_L12)
- **Framebuffer (ABL)**: 0xB8000000 (1080×2400, stride 4320, 16.6 MB)
- **Canvas for iOS**: 1125×2436 (3× scale = 375×812 pts)

## GPU - Adreno 730 (Gen 7.4.0)
- **Compatible**: `qcom,adreno-gpu-gen7-4-0` `qcom,kgsl-3d0`
- **Registers**:
  - 0x03d00000 / 0x40000 (core)
  - 0x03d61000 / 0x800
  - 0x03d50000 / 0x1000
  - 0x03d8b000 / 0x2000
  - 0x03d9e000 / 0x1000
  - 0x10900000 / 0x1000
- **Interrupts**: SPI 0x12c (300), 0x11e (286)
- **GMU**: Present (0x3d690000)
- **SMMU**: kgsl-iommu @ 0x3da0000
- **Power domains**: Multiple GDSCs (0x3d9905c, 0x3d99108)
- **Zap shader**: Supported (TZ auth)
- **HFI**: Host Firmware Interface

## Touch - Goodix GT9916S (FTS)
- **Controller**: SPI @ 0x990000 (spi@990000)
- **Compatible**: `st,spigoodix,gt9916S`
- **SPI frequency**: 12 MHz
- **Chip select**: 0
- **IRQ**: GPIO controller 0x3c, pin 21, active low (flags 8)
- **Reset**: GPIO controller 0x3c, pin 20, active high (flags 0)
- **Resolution**: 1080 × 2400
- **FOD**: Supported (under-display fingerprint)
- **Config**: Multiple touch tuning arrays in DT
- **Linux driver**: `drivers/input/touchscreen/goodix_gt9916s.c`
- **Firmware**: goodix,config-name, goodix,firmware-name in DT

## Buttons
### gpio-keys
- **Power**: KEY_POWER (0x1000000000000), wakeup
- **Volume up**: KEY_VOLUMEUP
- **Volume down**: KEY_VOLUMEDOWN
- **Compatible**: `gpio-keys`

### PMIC Power Key (PMK8350)
- **Path**: `/soc/c42d000.qcom,spmi/spmi-0/0-00/c42d000.qcom,spmi:qcom,pmk8350@0:pon_hlos@1300:pwrkey`
- **Compatible**: `qcom,pmk8350-pwrkey`
- **Interrupt**: PMIC IRQ via SPMI
- **Also**: resin (reset), bark (long press), resin+bark combos

## Wi-Fi / Bluetooth - QCA6490
### PCIe (Wi-Fi)
- **PCIe0**: 0x1c00000 (`qcom,pcie-msm`, `qcom,pci-msm`)
- **Root port**: pcie0_rp
  - **cnss_pci**: `qcom,cnss-pci` (Wi-Fi endpoint)
  - **IOMMU group**: Present
- **PCIe1**: 0x1c08000 (second controller, possibly unused)
- **MSI**: qcom,pcie0_msi, qcom,pcie1_msi @ 0x17110040
- **Phy**: qcom,pcie-phy-ver, qcom,phy-sequence (984 bytes)

### Bluetooth
- **Node**: bt_qca6490
- **Compatible**: `qcom,qca6490`
- **Mailboxes**: Present
- **GPIOs**:
  - bt-reset-gpio
  - bt-sw-ctrl-gpio
- **Power supplies**: Multiple VDD (AON, ASD, DIG, IO, RFA 0.8/1/2, RFCMN)
- **VREG**: IPA regulator
- **Wake GPIO**: Present
- **XO clock GPIO**: Present
- **WL reset GPIO**: Shared with Wi-Fi

## Audio - waipio-mtp ADSP
- **Sound card**: `waipio-mtp-snd-card`
- **Platform**: `soc:spf_core_platform`
- **Inputs**: Headset Jack, Button Jack, USB 3.5 Jack
- **Haptics**: `qcom-hv-haptics` (PMIC SPMI)
- **Codecs**: HDMI, DBA codec
- **DAI**: qcom,msm-dai-q6-hdmi

## UFS Storage
- **Controller**: ufshc @ 0x1d84000
- **Compatible**: `qcom,ufshc`
- **Partitions**: Super (dynamic), userdata (16GB+), boot, dtbo, vendor_boot, etc.
- **Dynamic partitions**: super -> logical partitions (system, vendor, product, etc.)

## SPMI / PMIC
- **SPMI controller**: 0xc42d000 (`qcom,spmi-pmic`)
- **PMIC**: PMK8350 (0-00 on SPMI bus 0)
- **Sub-devices**: Multiple (pon, buck, ldo, charger, haptics, etc.)

## PCIe / IOMMU
- **SMMU**: Multiple (apps-smmu @ 0x15000000, kgsl-iommu, pcie iommu)
- **IOMMU map**: Present for PCIe devices
- **Stream ID base**: Configurable per device

## Clocks / Power
- **Clock controllers**: Multiple @ 0x0, 0x100000, 0x3d90000, 0xaaf0000, 0xade0000, 0xaf00000
- **RPMh**: Present for power management
- **GDSC**: Multiple power domains
- **BCL**: Battery current limiting

## Sensors
- **Fingerprint**: goodix (separate from touch)
- **Touch**: xiaomi-touch (panel primary)

## Bootloader / Firmware
- **ABL**: Xiaomi bootloader (unlocked)
- **UEFI**: uefi_a @ sde1, uefi_b @ sde30
- **XBL**: xbl_a @ sdb1, xbl_b @ sdc1
- **TZ**: tz_a @ sde5, tz_b @ sde34
- **Hyp**: hyp_a @ sde6, hyp_b @ sde35
- **Modem**: modem_a @ sde7, modem_b @ sde36
- **DSP**: dsp_a @ sde12, dsp_b @ sde41

## Kernel Command Line (Android)
```
stack_depot_disable=on kasan.stacktrace=off kvm-arm.mode=protected
cgroup_disable=pressure cgroup.memory=nokmem console=ttyMSM0,115200n8 loglevel=6
kpti=0 log_buf_len=256K kernel.panic_on_rcu_stall=1 swiotlb=noforce
loop.max_part=7 pcie_ports=compat msm_rtb.filter=0x237
allow_mismatched_32bit_el0 kasan=off rcupdate.rcu_expedited=1
rcu_nocbs=0-7 ftrace_dump_on_oops pstore.compress=none
cpufreq.default_governor=performance video=vfb:640x400,bpp=32,memsize=3072000
disable_dma32=on mtdoops.fingerprint=23.2-20260617-NIGHTLY-diting
bootconfig bootinfo.pureason=0x40001 bootinfo.pdreason=0x2
debug_ext.initrd_size=14781 hwid.hwid_value=1638400 hwid.project=10
hwid.build_adc=34277 hwid.project_adc=4462
msm_drm.dsi_display0=qcom,mdss_dsi_l12_36_02_0b_dsc_cmd:
msm_drm.oled_wp=7f807f msm_drm.debugpolicy=0x20
rootwait ro init=/init
```

## Differences from mayfly (Xiaomi 12S)

| Component | mayfly | diting | Action |
|-----------|--------|--------|--------|
| Touch | ST FingerTip (FTS) SPI | Goodix GT9916S SPI | New driver |
| Buttons | PMIC arbiter v7 | gpio-keys + PMIC pwrkey | New driver |
| Audio | AW88261 (ADSP) | waipio-mtp (ADSP) | New driver |
| Panel | Generic | L12 specific | DT timing |
| Fingerprint | Goodix (separate) | Goodix (separate) | Same |
| Everything else | IDENTICAL | IDENTICAL | Reuse |

## References
- Linux kernel source: `drivers/input/touchscreen/goodix_gt9916s.c`
- Linux kernel source: `drivers/input/keyboard/gpio_keys.c`
- Linux kernel source: `drivers/spi/spi-qcom-geni.c`
- Linux kernel source: `drivers/pinctrl/qcom/pinctrl-sm8475.c`
- HakiOS mayfly: `drivers/input/hakios.stfts.c`, `drivers/input/hakios.keys.c`
- ios-sweet: `bsd/dev/sweet_touch.c`, `bsd/dev/sweet_keys.c`