#!/usr/bin/env python3
"""Build the minimal Apple Device Tree for diting (Xiaomi 12T Pro, SM8475).

Based on hakios-mayfly mkadt.py and ios-sweet mkadt.py.
Only what the early boot path actually reads; every MMIO address comes from the diting live FDT.
Usage:  mkadt.py OUT.adt [--dump] [--qemu] [--highmem]
"""
import hashlib, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adt  # noqa: E402

# Kernel-managed RAM: above every Qualcomm XPU carve-out
# diting has 12GB RAM: 4GB low + 8GB high
PHYS_BASE = 0x80000000
MEM_SIZE = 0x100000000  # 4GB low bank
# Panic log buffer, carved from the TOP of the dram range
PANIC_LOG_SIZE = 0x100000
# --highmem (phone only): the whole upper DDR bank
HIGH_PHYS_BASE = 0x100000000
HIGH_MEM_SIZE = 0x200000000  # 8GB high bank (12GB total - 4GB low)
# /arm-io children are relative to this; it must not be 0
SOC_BASE = 0x00000000  # Physical addresses on SM8475

# GICv3 addresses from diting device tree
GICD, GICD_SIZE = 0x17a00000, 0x10000
GICR, GICR_SIZE = 0x17a60000, 0x100000

# Framebuffer: ABL panel memory at 0xB8000000 (same as mayfly)
FB, FB_SIZE = 0xB8000000, 0x1700000
DITING_ECID = 0x444954494E470001  # 'DITING' + 1, synthetic
FB_W, FB_H, FB_STRIDE = 1080, 2400, 1080 * 4

# Internal UFS host (ufshc@1d84000)
UFS, UFS_SIZE = 0x1d84000, 0x3000
TIMEBASE = 19200000
VTIMER_INTID = 19  # Virtual timer interrupt

# QEMU virt (-M virt,gic-version=3 -cpu cortex-a76)
QEMU_GICD, QEMU_GICR, QEMU_TIMEBASE = 0x08000000, 0x080a0000, 62500000
QEMU_VTIMER_INTID = 27

BOOT_MANIFEST_HASH = hashlib.sha384(b'diting boot manifest').digest()

# iPhone X (iPhone10,3 / D22AP) IPSW userland
D22AP_ADT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../ios-sweet/research/ipsw-x/d22ap.adt')


def d22ap_product(path=D22AP_ADT):
    """/product properties of the real D22AP tree."""
    if not os.path.exists(path):
        print(f'warning: {path} missing, no /product node', file=sys.stderr)
        return None
    root, _ = adt.parse(open(path, 'rb').read())
    for c in root.children:
        if dict((k, v) for k, f, v in c.props).get('name') == b'product\0':
            return [(k, v) for k, f, v in c.props if not f and k not in ('name', 'AAPL,phandle')]
    raise SystemExit(f'{path}: no /product node')


u32 = lambda *v: struct.pack('<%dI' % len(v), *v)
u64 = lambda *v: struct.pack('<%dQ' % len(v), *v)
cstr = lambda s: s.encode() + b'\0'


def node(name, props=(), children=()):
    n = adt.Node()
    n.props = [('name', 0, cstr(name))] + [(k, 0, v) for k, v in props]
    n.children = list(children)
    return n


def build(seed=None, qemu=False, highmem=False):
    """qemu=True: same tree, but with QEMU virt's GIC addresses and CNTFRQ."""
    phys_base, mem_size = (HIGH_PHYS_BASE, HIGH_MEM_SIZE) if highmem else (PHYS_BASE, MEM_SIZE)
    # Carve the panic log off the top so the kernel never allocates over it.
    panic_base = phys_base + mem_size - PANIC_LOG_SIZE
    mem_size -= PANIC_LOG_SIZE
    gicd, gicr, timebase = (QEMU_GICD, QEMU_GICR, QEMU_TIMEBASE) if qemu else (GICD, GICR, TIMEBASE)
    seed = seed if seed is not None else os.urandom(64)
    phandle = iter(range(1, 1000))
    ph = lambda: ('AAPL,phandle', u32(next(phandle)))

    chosen = node('chosen', [
        ph(),
        ('dram-base', u64(phys_base)),
        ('dram-size', u64(mem_size)),
        ('random-seed', seed),
        ('debug-enabled', u32(1)),
        ('embedded-panic-log-size', u32(PANIC_LOG_SIZE)),
        ('firmware-version', cstr('diting-shim')),
        ('system-firmware-version', cstr('diting-shim')),
        ('boot-manifest-hash', BOOT_MANIFEST_HASH),
        ('crypto-hash-method', cstr('sha2-384')),
        # 1080x2400 @3x = 360x800 points (like iPhone X class devices)
        ('display-scale', u32(3)),
        # XNU derives IOPlatformUUID from these on arm
        ('unique-chip-id', struct.pack('<Q', DITING_ECID)),
        ('chip-id', u32(0x8015)),  # A11 chip-id for iPhone X userland
        # Security status as on a dev-fused, undemoted board
        ('certificate-production-status', u32(0)),
        ('effective-production-status-ap', u32(0)),
        ('certificate-security-mode', u32(1)),
        ('effective-security-mode-sep', u32(1)),
    ], [
        node('memory-map', [ph()]),
        node('asmb', [ph(), ('lp-sip0', u64(0x6f)), ('lp-sip1', u32(1))]),
    ])

    # DITING SMP: 8 cores in physical-core order
    # Cluster 0: 4x Cortex-A510 (efficiency) @ 1.8 GHz - MPIDR 0x000-0x300
    # Cluster 1: 3x Cortex-A710 (performance) @ 2.75 GHz - MPIDR 0x100-0x300
    # Cluster 2: 1x Cortex-X2 (prime) @ 3.19 GHz - MPIDR 0x400
    cpu_nodes = []
    # Cluster 0: 4x A510
    for core in range(4):
        cpu_nodes.append(node('cpu%d' % core, [
            ph(),
            ('device_type', cstr('cpu')),
            ('compatible', cstr('qcom,kryo-8-10') + cstr('ARM,v8')),  # A510
            ('reg', u32(core << 8)),
            ('cpu-id', u32(core)),
            ('cluster-id', u32(0)),
            ('cluster-type', u32(0)),  # homogeneous SMP
            ('die-cluster-id', u32(0)),
            ('cluster-core-id', u32(core)),
            ('l2-cache-id', u32(core)),
            ('l3-cache-id', u32(0)),
            ('state', cstr('running' if core == 0 else 'stopped')),
            ('timebase-frequency', u32(timebase)),
            ('clock-frequency', u32(1804800000)),  # 1.8 GHz
            ('bus-frequency', u32(100000000)),
            ('memory-frequency', u32(3200000000)),
            ('peripheral-frequency', u32(timebase)),
            ('fixed-frequency', u32(timebase)),
        ]))
    # Cluster 1: 3x A710
    for i, core in enumerate(range(4, 7)):
        cpu_nodes.append(node('cpu%d' % core, [
            ph(),
            ('device_type', cstr('cpu')),
            ('compatible', cstr('qcom,kryo-8-70') + cstr('ARM,v8')),  # A710
            ('reg', u32((i + 1) << 8)),  # MPIDR 0x100, 0x200, 0x300
            ('cpu-id', u32(core)),
            ('cluster-id', u32(1)),
            ('cluster-type', u32(0)),
            ('die-cluster-id', u32(0)),
            ('cluster-core-id', u32(i)),
            ('l2-cache-id', u32(core)),
            ('l3-cache-id', u32(0)),
            ('state', cstr('stopped')),
            ('timebase-frequency', u32(timebase)),
            ('clock-frequency', u32(2750000000)),  # 2.75 GHz
            ('bus-frequency', u32(100000000)),
            ('memory-frequency', u32(3200000000)),
            ('peripheral-frequency', u32(timebase)),
            ('fixed-frequency', u32(timebase)),
        ]))
    # Cluster 2: 1x X2 (prime)
    cpu_nodes.append(node('cpu7', [
        ph(),
        ('device_type', cstr('cpu')),
        ('compatible', cstr('qcom,kryo-8-20') + cstr('ARM,v8')),  # X2
        ('reg', u32(0x400)),  # MPIDR 0x400
        ('cpu-id', u32(7)),
        ('cluster-id', u32(2)),
        ('cluster-type', u32(0)),
        ('die-cluster-id', u32(0)),
        ('cluster-core-id', u32(0)),
        ('l2-cache-id', u32(7)),
        ('l3-cache-id', u32(0)),
        ('state', cstr('stopped')),
        ('timebase-frequency', u32(timebase)),
        ('clock-frequency', u32(3190000000)),  # 3.19 GHz
        ('bus-frequency', u32(100000000)),
        ('memory-frequency', u32(3200000000)),
        ('peripheral-frequency', u32(timebase)),
        ('fixed-frequency', u32(timebase)),
    ]))

    cpus = node('cpus', [ph(), ('#address-cells', u32(1)), ('#size-cells', u32(0))], cpu_nodes)

    gic = node('gic', [
        ph(),
        ('compatible', cstr('arm,gic-v3')),
        ('interrupt-controller', b''),
        ('virtual-timer-intid', u32(QEMU_VTIMER_INTID if qemu else VTIMER_INTID)),
        ('reg', u64(gicd - SOC_BASE, GICD_SIZE, gicr - SOC_BASE, GICR_SIZE)),
    ])

    # Build arm-io children separately for clarity
    pwrkey_node = node('pwrkey', [
        ph(),
        ('compatible', cstr('qcom,pmk8350-pwrkey')),
        ('interrupt-parent', u32(0x3c)),
        ('interrupts', u32(19, 4)),
    ])

    pmic_node = node('pmic@0', [
        ph(),
        ('compatible', cstr('qcom,pmk8350')),
        ('reg', u32(0)),
    ], [pwrkey_node])

    spmi_node = node('spmi', [
        ph(),
        ('compatible', cstr('qcom,spmi-pmic')),
        ('reg', u64(0x0c42d000, 0x10000)),
        ('interrupts', u32(0, 0x12c, 4)),
    ], [pmic_node])

    touch_node = node('touch@0', [
        ph(),
        ('compatible', cstr('goodix,gt9916s')),
        ('reg', u32(0)),
        ('spi-max-frequency', u32(12000000)),
        ('interrupt-parent', u32(0x3c)),
        ('interrupts', u32(21, 8)),
        ('reset-gpios', u32(0x3c, 20, 0)),
        ('irq-gpios', u32(0x3c, 21, 8)),
        ('goodix,x-max', u32(1080)),
        ('goodix,y-max', u32(2400)),
    ])

    spi0_node = node('spi0', [
        ph(),
        ('compatible', cstr('qcom,geni-spi')),
        ('reg', u64(0x990000, 0x10000)),
        ('interrupts', u32(0, 0x12c, 4)),
        ('qcom,spi-max-frequency', u32(12000000)),
    ], [touch_node])

    cnss_pci_node = node('cnss_pci', [
        ph(),
        ('compatible', cstr('qcom,cnss-pci')),
        ('device_type', cstr('wifi')),
        ('reg', u64(0, 0, 0, 0, 0)),
    ])

    pcie0_node = node('pcie0', [
        ph(),
        ('compatible', cstr('qcom,pcie-msm')),
        ('device_type', cstr('pci')),
        ('reg', u64(0x1c00000, 0x8000)),
        ('interrupts', u32(0, 0x12c, 4)),
        ('qcom,ep-latency', u32(0)),
        ('qcom,num-parf-testbus-sel', u32(1)),
    ], [cnss_pci_node])

    gpu_node = node('gpu', [
        ph(),
        ('compatible', cstr('qcom,adreno-gpu-gen7-4-0') + cstr('qcom,kgsl-3d0')),
        ('device_type', cstr('gpu')),
        ('reg', u64(0x03d00000, 0x40000,
                     0x03d61000, 0x800,
                     0x03d50000, 0x1000,
                     0x03d8b000, 0x2000,
                     0x03d9e000, 0x1000,
                     0x10900000, 0x1000)),
        ('interrupts', u32(0, 0x12c, 4, 0, 0x11e, 4)),
        ('qcom,gmu', u32(1)),
        ('qcom,zap-shader', u32(1)),
    ])

    ufs_node = node('ufs', [
        ph(),
        ('compatible', cstr('qcom,ufshc')),
        ('reg', u64(UFS, UFS_SIZE)),
    ])

    disp0_node = node('disp0', [
        ph(),
        ('device_type', cstr('display-subsystem')),
        ('compatible', cstr('diting,display')),
        ('canvas-width', u32(1125)),
        ('canvas-height', u32(2436)),
    ])

    wdt_node = node('wdt', [ph(), ('no-pmu', u32(1))])

    adsp_node = node('adsp', [
        ph(),
        ('compatible', cstr('qcom,waipio-mtp')),
        ('device_type', cstr('audio-dsp')),
        ('reg', u64(0x0a000000, 0x1000000)),
        ('interrupts', u32(0, 0x12c, 4)),
    ])

    arm_io_children = [gic, wdt_node, disp0_node, gpu_node, ufs_node, pcie0_node, spi0_node, spmi_node, adsp_node]

    arm_io = node('arm-io', [
        ph(),
        ('device_type', cstr('diting-io')),
        ('compatible', cstr('diting-io') + cstr('arm-io')),
        ('#address-cells', u32(2)),
        ('#size-cells', u32(2)),
        ('ranges', u64(0, SOC_BASE, 0x100000000 - SOC_BASE)),
    ], arm_io_children)

    fbcon = node('diting-fbcon', [
        ph(),
        ('reg', u64(FB, FB_SIZE)),
        ('width', u32(FB_W)),
        ('height', u32(FB_H)),
        ('stride', u32(FB_STRIDE)),
    ])

    ufs = node('diting-ufs', [
        ph(),
        ('compatible', cstr('qcom,ufshc')),
        ('reg', u64(UFS, UFS_SIZE)),
    ])

    defaults = node('defaults', [ph(), ('no-effaceable-storage', u32(1))])

    buttons = node('buttons', [
        ph(),
        ('button-names', cstr('volup') + cstr('voldown') + cstr('hold')),
        ('home-button-type', u32(2)),
        ('opposed-power-vol-buttons', u32(1)),
    ])

    product_props = d22ap_product()
    product = [node('product', [ph()] + product_props)] if product_props else []

    pram = node('pram', [ph(), ('reg', u64(panic_base) + u64(PANIC_LOG_SIZE))])

    return node('device-tree', [
        ph(),
        ('compatible', cstr('D22AP') + cstr('iPhone10,3') + cstr('xiaomi,diting') + cstr('qcom,sm8475') + cstr('AppleARM')),
        ('model', cstr('iPhone10,3')),
        ('target-type', cstr('D22')),
        ('target-sub-type', cstr('D22AP')),
        ('manufacturer', cstr('Apple Inc.')),
        ('#address-cells', u32(2)),
        ('#size-cells', u32(2)),
    ], [chosen, defaults, cpus, arm_io, fbcon, buttons, pram] + product + ([] if qemu else [ufs]))


if __name__ == '__main__':
    root = build(qemu='--qemu' in sys.argv, highmem='--highmem' in sys.argv)
    blob = adt.serialize(root)
    open(sys.argv[1], 'wb').write(blob)
    if '--dump' in sys.argv:
        adt.dump(adt.parse(blob)[0])
    print(f'{sys.argv[1]}: {len(blob)} bytes', file=sys.stderr)