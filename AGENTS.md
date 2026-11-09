# Working on hakios-diting

- Read `NOTES.md` before starting; it contains the project goal, hardware facts,
  current blocker, local artifact locations and the next concrete action.
- The user switches agents frequently. Update the active handoff in `NOTES.md`
  after each milestone and before stopping. Record commits, CI run IDs, exact
  build/boot results and unfinished work. Distinguish observations from guesses.
- Commit completed changes. Use `gh` for GitHub Actions kernel builds and logs.
  Local single-file cross-compiles are useful before spending a CI run.
- Device bring-up uses temporary `fastboot boot` images. Preserve the Android
  installation and partition backups. The user approved using internal UFS for
  iOS and said Android may be deleted: the iOS root goes into the existing
  `userdata` partition (no GPT changes). Keep bootloaders, recovery, modem,
  persist and the backups intact, and confirm each destructive step with the
  user before running it.
- Keep device dumps, serial numbers and downloaded Apple artifacts out of git.

## Repository Structure

```
hakios-diting/
├── AGENTS.md              # This file
├── NOTES.md               # Active handoff and work log
├── README.md              # Project overview
├── PORTING_PLAN.md        # Full porting plan
├── configs/
│   └── diting_defconfig   # XNU kernel config
├── tools/
│   ├── adt.py             # ADT serialization (from ios-sweet)
│   ├── mkadt.py           # Build Apple Device Tree for diting
│   ├── build-image.sh     # Build boot image (kernel + ADT + cmdline)
│   ├── run.sh             # Boot on device and collect logs
│   └── diting-log-pull.sh # Pull kernel log from userdata
├── docs/
│   ├── FINDINGS.md        # Hardware register-level findings
│   ├── HISTORY.md         # Bring-up timeline
│   ├── BOOT-ARGS.md       # Boot arguments reference
│   ├── FIRMWARE.md        # Required firmware files
│   └── OPEN-ISSUES.md     # Known issues
└── reference/
    └── android/           # Android dmesg, live DT, iomem, partitions
```

## Build Workflow

### Kernel (on macOS via GitHub Actions)
```bash
# In hakios-xnu-kernel fork (mayfly-port branch)
make diting_defconfig
make kernel
# CI builds ~8 min, downloads to xnu/out/
```

### ADT (on Linux)
```bash
cd hakios-diting
python3 tools/mkadt.py out/diting.adt --highmem
```

### Boot Image (on Linux)
```bash
./tools/build-image.sh daily "boot args here"
# Output: out/shim-boot-daily.img
```

### Boot on Device
```bash
# Device in fastboot mode
fastboot boot out/shim-boot-daily.img
```

### Log Collection
```bash
# Option 1: USB networking (if ditingusb=2)
nc -ul 5140 > logs/live.txt

# Option 2: Recovery mode (after boot)
fastboot boot recovery/recovery.img
# wait for adb
./tools/diting-log-pull.sh logs/boot.txt
adb reboot bootloader
```

## Key Files to Modify

| Task | File(s) |
|------|---------|
| ADT changes | `tools/mkadt.py` |
| Kernel config | `configs/diting_defconfig` |
| Boot args | `tools/build-image.sh` |
| Touch driver | `../hakios-xnu-kernel/drivers/input/hakios.diting_touch.c` |
| Buttons driver | `../hakios-xnu-kernel/drivers/input/hakios.diting_keys.c` |
| Audio driver | `../hakios-xnu-kernel/drivers/audio/hakios.diting_audio.c` |
| SoC init | `../hakios-xnu-kernel/socs/sm8475/diting.c` |
| UEFI | `../hakios-uefi/ditingPkg/` |

## Debugging Tips

- Boot arg `ditingfb_noconsole=1` hides kernel text over GUI (but hides panics too)
- Boot arg `ditingusb=2` enables CDC-ECM USB networking at 192.168.7.2
- Boot arg `fb_hud=1` shows FPS counter
- Kernel console at 115200 on ttyMSM0 (USB serial)
- Persistent log in last 4 MiB of userdata (pull via recovery)
- QEMU smoke test: `python3 ../hakios-xnu-kernel/tools/qemu-sweet.py ...`

## Commit Convention

```
<subsystem>: <short description>

<details>

Co-Authored-By: claude <noreply@anthropic.com>
```