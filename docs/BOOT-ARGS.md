# Boot Arguments Reference - diting

## Required (minimal boot)
```
rd=ufsroot0 ufsrw=1 rootrw=1          # Root on userdata, writable
cpus=7                                 # Enable 7 cores (skip prime core initially)
launchd_unsecure_cache=1               # Skip AMFI verification
wdt=-1                                 # Disable hardware watchdog
```

## Display
```
ditingfb_noconsole=1                   # Don't draw kernel text over GUI (hides panics!)
ditingfb_hz=30                         # Panel copy rate (30 Hz = 60 Hz vsync / 2)
```

## USB
```
ditingusb=2                            # CDC-ECM USB networking (192.168.7.2)
```

## Audio (waipio-mtp ADSP)
```
adsp=1                                 # Enable ADSP
sound=4                                # Audio config
sound_sd=2
sound_below=80
sound_gain=0
speaker_sr=8
```

## Bluetooth (QCA6490)
```
qcabt=6                                # QCA BT H4 transport
```

## Wi-Fi (QCA6490 PCIe)
```
wifi_pcie=12                           # PCIe bring-up steps
wifi_lx=2                              # LX firmware
wifi_station=1                         # Station mode
wifi_read_ms=0
wifi_wait_ms=10000
wifi_mac=<MAC_FROM_PERSIST>            # REQUIRED: Wi-Fi MAC from persist partition
```

## Debug / HUD
```
fb_hud=1                               # Show FPS counter
cpu_mhz=2400                           # CPU frequency cap (MHz)
```

## Kernel Debug
```
debug=0xc                              # Kernel debug flags
serial=3                               # Serial console
keepsyms=1                             # Keep kernel symbols
-enable_kprintf_spam                   # Verbose kprintf
-noprogress                            # Hide boot progress
```

## Full Recommended Command Line
```
rd=ufsroot0 ufsrw=1 rootrw=1 cpus=7 launchd_unsecure_cache=1 wdt=-1 ditingfb_noconsole=1 ditingfb_hz=30 ditingusb=2 adsp=1 sound=4 sound_sd=2 sound_below=80 sound_gain=0 speaker_sr=8 qcabt=6 wifi_pcie=12 wifi_lx=2 wifi_station=1 wifi_read_ms=0 wifi_wait_ms=10000 wifi_mac=<YOUR_MAC> fb_hud=1 cpu_mhz=2400
```

## Argument Details

### `cpus=N`
- N = 1..7 (8 cores total, prime core is cpu7)
- Start with 1 for debugging, increase to 7 for performance
- Prime core (X2) may need special handling

### `ditingfb_noconsole=1`
- Hides kernel console text over the GUI
- **WARNING**: Also hides kernel panics on screen!
- Use `ditingfb_noconsole=0` for debugging panics

### `ditingfb_hz=N`
- Panel copy frequency from vsync timer
- Default 30 (60 Hz display / 2)
- Higher = smoother but more CPU

### `ditingusb=N`
- 0 = disabled
- 1 = USB device mode only (fastboot)
- 2 = CDC-ECM networking at 192.168.7.2 (for live logs)

### `wifi_mac=XX:XX:XX:XX:XX:XX`
- **REQUIRED** for Wi-Fi
- Extract from persist partition: `qca6490/wlan_mac.bin`
- Without it, ath11k stops with "IT HAS NO ADDRESS"

### `fb_hud=1`
- Shows frame counter on screen
- Useful for verifying display refresh

### `cpu_mhz=N`
- Cap CPU frequency for thermal/power testing
- 2400 = 2.4 GHz cap

## QEMU Testing
For QEMU, use different args:
```
rd=md0 debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress
```
And QEMU ADT: `python3 tools/mkadt.py qemu.adt --qemu`