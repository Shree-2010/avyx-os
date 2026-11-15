#!/usr/bin/env python3
"""Install test.

Phase A: boot the live ISO (UEFI) with a blank virtual disk, let the image start the Calamares
         installer (CI-only autostart, enabled by DMI family AVYX-CI-INSTALL), and drive it with
         keyboard input over QMP until the exec phase finishes.
Phase B: boot ONLY the installed disk (no ISO) and check it reaches the desktop and is no longer
         running the live image.

Screenshots of every step go to --out so failures can be diagnosed. Standard library only.
Exit code 0 only if phase B reached the desktop from the installed disk.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qemu_shots import Qmp, find_ovmf  # noqa: E402

SHIFT_CHARS = {c: c.lower() for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
SYMBOLS = {" ": "spc", "-": "minus", ".": "dot", "_": ("shift", "minus")}


class Vm:
    def __init__(self, tag, out, iso, disk, ovmf_vars, family, timeout, smp=2, mem=4096, cpu="SandyBridge"):
        self.tag, self.out, self.iso, self.disk = tag, Path(out), iso, disk
        self.family, self.timeout = family, timeout
        self.smp, self.mem, self.cpu = smp, mem, cpu
        self.ovmf_vars = ovmf_vars
        self.marks = {}
        self.seen = 0
        self.nshot = 0
        self.t0 = time.time()
        self.shots = []

    def start(self):
        o = self.out
        self.serial, self.mlog = o / f"serial-{self.tag}.log", o / f"marks-{self.tag}.log"
        self.sock = o / f"qmp-{self.tag}.sock"
        for p in (self.serial, self.mlog, self.sock):
            if p.exists():
                p.unlink()
        kvm = os.path.exists("/dev/kvm") and os.access("/dev/kvm", os.R_OK | os.W_OK)
        self.kvm = kvm
        code, _ = find_ovmf()
        cmd = [
            "qemu-system-x86_64", "-machine", "q35", "-accel", "kvm" if kvm else "tcg,thread=multi",
            "-cpu", self.cpu, "-smp", str(self.smp), "-m", str(self.mem), "-display", "none", "-vga", "std",
            "-serial", f"file:{self.serial}", "-serial", f"file:{self.mlog}",
            "-smbios", f"type=1,serial=AVYX-CI,family={self.family}",
            "-qmp", f"unix:{self.sock},server=on,wait=off",
            "-no-reboot", "-nic", "user,model=e1000", "-device", "virtio-rng-pci",
            "-drive", f"file={self.disk},if=none,id=hd0,format=qcow2", "-device", "virtio-blk-pci,drive=hd0",
            "-drive", f"if=pflash,format=raw,unit=0,readonly=on,file={code}",
            "-drive", f"if=pflash,format=raw,unit=1,file={self.ovmf_vars}",
        ]
        if self.iso:
            cmd += ["-cdrom", self.iso, "-boot", "order=d"]
        else:
            cmd += ["-boot", "order=c"]
        print(f"[{self.tag}] QEMU:", " ".join(cmd), flush=True)
        self.qlog = open(o / f"qemu-{self.tag}.log", "w")
        self.proc = subprocess.Popen(cmd, stdout=self.qlog, stderr=subprocess.STDOUT)
        self.qmp = Qmp(str(self.sock))
        self.t0 = time.time()

    def alive(self):
        return self.proc.poll() is None

    def elapsed(self):
        return time.time() - self.t0

    def pump(self):
        if not self.mlog.exists():
            return
        with open(self.mlog, "rb") as f:
            f.seek(self.seen)
            chunk = f.read()
            self.seen += len(chunk)
        for line in chunk.decode("utf-8", "replace").splitlines():
            m = re.search(r"AVYX_MARK\s+(\S+)", line)
            if m:
                name = m.group(1).rstrip(":")
                self.marks.setdefault(name, {"wall_s": round(self.elapsed(), 1), "line": line.strip()})
                print(f"[{self.tag} {self.elapsed():7.1f}s] {line.strip()}", flush=True)

    def shot(self, label):
        if not self.alive():
            return
        self.nshot += 1
        png = self.out / f"{self.tag}-{self.nshot:03d}-{label}.png"
        try:
            r = self.qmp.cmd("screendump", filename=str(png), format="png")
            if "error" in r:
                ppm = png.with_suffix(".ppm")
                self.qmp.cmd("screendump", filename=str(ppm))
                if shutil.which("convert") and ppm.exists():
                    subprocess.run(["convert", str(ppm), str(png)], check=False)
                    ppm.unlink()
        except Exception as e:  # noqa: BLE001
            print("screenshot failed:", e)
            return
        if png.exists():
            self.shots.append(png.name)

    def key(self, *keys, hold=120):
        flat = []
        for k in keys:
            flat.extend(k if isinstance(k, tuple) else (k,))
        self.qmp.cmd("send-key", keys=[{"type": "qcode", "data": k} for k in flat], **{"hold-time": hold})
        time.sleep(0.25)

    def text(self, s):
        for ch in s:
            if ch in SHIFT_CHARS:
                self.key("shift", SHIFT_CHARS[ch])
            elif ch in SYMBOLS:
                self.key(SYMBOLS[ch])
            else:
                self.key(ch)

    def sleep(self, secs, shot_label=None, every=10):
        end = time.time() + secs
        nxt = time.time()
        while time.time() < end and self.alive():
            self.pump()
            if shot_label and time.time() >= nxt:
                self.shot(shot_label)
                nxt = time.time() + every
            time.sleep(0.5)

    def wait_mark(self, name, timeout, shot_label=None, every=20):
        end = time.time() + timeout
        nxt = time.time()
        while time.time() < end:
            self.pump()
            if name in self.marks:
                return True
            if not self.alive():
                return False
            if shot_label and time.time() >= nxt:
                self.shot(shot_label)
                nxt = time.time() + every
            time.sleep(0.5)
        return False

    def stop(self):
        try:
            self.shot("final")
            self.qmp.cmd("quit")
        except Exception:  # noqa: BLE001
            pass
        try:
            self.proc.wait(timeout=20)
        except Exception:  # noqa: BLE001
            self.proc.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--disk-gb", type=int, default=20)
    ap.add_argument("--install-timeout", type=int, default=1500)
    ap.add_argument("--boot-timeout", type=int, default=480)
    ap.add_argument("--username", default="avyx")
    ap.add_argument("--password", default="avyx1234")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    disk = out / "target-disk.qcow2"
    subprocess.run(["qemu-img", "create", "-f", "qcow2", str(disk), f"{args.disk_gb}G"], check=True, stdout=subprocess.DEVNULL)
    _, varsf = find_ovmf()
    nvram = out / "OVMF_VARS-install.fd"
    shutil.copy(varsf, nvram)

    result = {"disk_gb": args.disk_gb, "phase_a": {}, "phase_b": {}, "installed_ok": False}

    # ------------------------------------------------------------------ phase A
    a = Vm("install", out, args.iso, disk, nvram, "AVYX-CI-INSTALL", args.install_timeout)
    a.start()
    try:
        ok = a.wait_mark("plasmashell_started", 420, "live-boot", every=30)
        result["phase_a"]["live_desktop"] = ok
        if not ok:
            a.sleep(20)
            raise RuntimeError("live desktop never started")
        ok = a.wait_mark("calamares_launch", 90)
        result["phase_a"]["installer_launched"] = ok
        a.sleep(35, "installer-starting", every=12)

        # Welcome -> Location -> Keyboard -> Partitions
        for step in ("welcome", "location", "keyboard"):
            a.shot(step)
            a.key("alt", "n")
            a.sleep(4)
        a.sleep(4)
        a.shot("partitions")
        a.key("alt", "n")
        a.sleep(4)

        # Users page. Fields are replaced with ctrl+a so the result does not depend on autofill.
        a.shot("users-empty")
        a.text("AVYX User")
        a.key("tab"); a.key("ctrl", "a"); a.text(args.username)
        a.key("tab"); a.key("ctrl", "a"); a.text("avyx-pc")
        a.key("tab"); a.text(args.password)
        a.key("tab"); a.text(args.password)
        a.key("tab"); a.key("spc")  # "log in automatically"
        a.sleep(1)
        a.shot("users-filled")
        a.key("alt", "n")
        a.sleep(4)

        # Summary -> Install -> confirm
        a.shot("summary")
        a.key("alt", "i")
        a.sleep(3)
        a.shot("confirm")
        a.key("ret")
        a.sleep(5)

        done = a.wait_mark("install_exec_done", args.install_timeout, "installing", every=45)
        result["phase_a"]["install_finished"] = done
        a.sleep(6)
        a.shot("finished-page")
        if done:
            a.key("alt", "d")  # Done (restart now is pre-checked; QEMU -no-reboot then exits)
            for _ in range(60):
                if not a.alive():
                    break
                time.sleep(1)
    except Exception as e:  # noqa: BLE001
        result["phase_a"]["error"] = str(e)
        print("phase A error:", e)
    finally:
        a.pump()
        result["phase_a"]["marks"] = {k: v["wall_s"] for k, v in a.marks.items()}
        result["phase_a"]["screenshots"] = a.shots
        result["accel"] = "kvm" if a.kvm else "tcg (software emulation, timings NOT representative)"
        a.stop()

    if not result["phase_a"].get("install_finished"):
        (out / "result-install.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # ------------------------------------------------------------------ phase B
    b = Vm("installed", out, None, disk, nvram, "AVYX-CI", args.boot_timeout)
    b.start()
    try:
        ok = b.wait_mark("plasmashell_started", args.boot_timeout, "installed-boot", every=30)
        result["phase_b"]["desktop"] = ok
        if ok:
            b.wait_mark("desktop_idle", 150)
            b.wait_mark("done", 60)
        else:
            b.wait_mark("done", 90)
        b.shot("installed-desktop")
    finally:
        b.pump()
        result["phase_b"]["marks"] = {k: v["wall_s"] for k, v in b.marks.items()}
        result["phase_b"]["screenshots"] = b.shots
        line = b.marks.get("rootfs", {}).get("line", "")
        result["phase_b"]["rootfs"] = line
        result["phase_b"]["boots_from_disk"] = bool(re.search(r"/dev/(vda|sda)\d*\s+(ext4|btrfs)", line))
        idle = b.marks.get("desktop_idle", {}).get("line", "")
        m = re.search(r"mem_used_mb=(\d+) mem_total_mb=(\d+)", idle)
        result["phase_b"]["idle_ram_used_mb"] = int(m.group(1)) if m else None
        b.stop()

    result["installed_ok"] = bool(result["phase_b"].get("desktop") and result["phase_b"].get("boots_from_disk"))
    (out / "result-install.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ("phase_a", "phase_b")}, indent=2))
    sys.exit(0 if result["installed_ok"] else 1)


if __name__ == "__main__":
    main()
