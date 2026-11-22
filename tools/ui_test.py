#!/usr/bin/env python3
"""UI interaction test (live ISO, UEFI): drives the desktop with keyboard and mouse over QMP and
saves a screenshot after every step, so what Spotlight-style search, the AVYX menu, the overview,
the dock and window decorations really do can be seen. Standard library only.
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from install_test import Vm  # noqa: E402
from qemu_shots import find_ovmf  # noqa: E402

W, H = 1280, 800


def move(vm, x, y):
    ax, ay = int(x / W * 32767), int(y / H * 32767)
    vm.qmp.cmd("input-send-event", events=[
        {"type": "abs", "data": {"axis": "x", "value": ax}},
        {"type": "abs", "data": {"axis": "y", "value": ay}}])
    time.sleep(0.3)


def click(vm, x, y, button="left"):
    move(vm, x, y)
    for down in (True, False):
        vm.qmp.cmd("input-send-event", events=[{"type": "btn", "data": {"down": down, "button": button}}])
        time.sleep(0.12)
    time.sleep(0.3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    disk = out / "ui-disk.qcow2"
    subprocess.run(["qemu-img", "create", "-f", "qcow2", str(disk), "2G"], check=True, stdout=subprocess.DEVNULL)
    _, varsf = find_ovmf()
    nvram = out / "OVMF_VARS-ui.fd"
    shutil.copy(varsf, nvram)

    vm = Vm("ui", out, args.iso, disk, nvram, "AVYX-CI-UI", 600,
            extra=["-device", "qemu-xhci", "-device", "usb-tablet"])
    vm.start()
    result = {"steps": []}

    def step(name, fn=None, wait=3.0):
        if fn:
            fn()
        vm.sleep(wait)
        vm.shot(name)
        result["steps"].append(name)

    try:
        ok = vm.wait_mark("plasmashell_started", 420, "boot", every=40)
        result["desktop"] = ok
        if not ok:
            raise RuntimeError("desktop never started")
        vm.wait_mark("done", 300)
        vm.sleep(3)
        step("01-desktop", wait=1)
        step("02-search-open", lambda: vm.key("alt", "spc"), 4)
        step("03-search-typed", lambda: vm.text("term"), 5)
        step("04-search-closed", lambda: vm.key("esc"), 2)
        step("05-launcher-key", lambda: vm.key("meta_l"), 4)
        step("06-launcher-closed", lambda: vm.key("esc"), 2)
        step("07-avyx-menu-click", lambda: click(vm, 14, 14), 4)
        step("08-avyx-menu-closed", lambda: vm.key("esc"), 2)
        step("09-overview", lambda: vm.key("meta_l", "w"), 4)
        step("10-overview-closed", lambda: vm.key("esc"), 2)
        step("11-dock-hover", lambda: move(vm, 520, 772), 2)
        step("12-dock-hover-2", lambda: move(vm, 640, 772), 2)
        step("13-open-from-dock", lambda: click(vm, 640, 772), 12)
        step("14-clock-click", lambda: click(vm, 1245, 14), 3)
        step("15-tray-click", lambda: click(vm, 1115, 14), 3)
        step("16-final", lambda: vm.key("esc"), 2)
    except Exception as e:  # noqa: BLE001
        result["error"] = str(e)
        print("ui test error:", e)
    finally:
        vm.pump()
        result["marks"] = {k: v["wall_s"] for k, v in vm.marks.items()}
        result["screenshots"] = vm.shots
        vm.stop()
    (out / "result-ui.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("desktop") and "error" not in result else 1)


if __name__ == "__main__":
    main()
