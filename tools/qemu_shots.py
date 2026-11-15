#!/usr/bin/env python3
"""Boot an ISO in QEMU (UEFI/OVMF or legacy BIOS), take screenshots over QMP, and record
measured milestones that the guest prints on its serial console (AVYX_MARK lines).

Standard library only. Exit code 0 only if the desktop (plasmashell) was reached.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path


def find_ovmf():
    pairs = [
        ("/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/OVMF/OVMF_VARS_4M.fd"),
        ("/usr/share/OVMF/OVMF_CODE.fd", "/usr/share/OVMF/OVMF_VARS.fd"),
        ("/usr/share/edk2/ovmf/OVMF_CODE.fd", "/usr/share/edk2/ovmf/OVMF_VARS.fd"),
        ("/usr/share/qemu/OVMF_CODE.fd", "/usr/share/qemu/OVMF_VARS.fd"),
    ]
    for code, varsf in pairs:
        if os.path.exists(code) and os.path.exists(varsf):
            return code, varsf
    sys.exit("OVMF firmware not found")


class Qmp:
    def __init__(self, path, wait=60):
        deadline = time.time() + wait
        last = None
        while time.time() < deadline:
            try:
                self.s = socket.socket(socket.AF_UNIX)
                self.s.connect(path)
                break
            except OSError as e:
                last = e
                time.sleep(0.5)
        else:
            raise RuntimeError(f"QMP socket never appeared: {last}")
        self.f = self.s.makefile("rw", buffering=1)
        self.f.readline()  # greeting
        self.cmd("qmp_capabilities")

    def cmd(self, name, **args):
        self.f.write(json.dumps({"execute": name, "arguments": args}) + "\n")
        while True:
            line = self.f.readline()
            if not line:
                raise RuntimeError("QMP closed")
            msg = json.loads(line)
            if "return" in msg or "error" in msg:
                return msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["uefi", "bios"], required=True)
    ap.add_argument("--timeout", type=int, default=1500)
    ap.add_argument("--mem", type=int, default=4096)
    ap.add_argument("--smp", type=int, default=2)
    ap.add_argument("--cpu", default="SandyBridge")
    args = ap.parse_args()

    out = Path(args.out)
    shots_dir = out / f"shots-{args.mode}"
    shots_dir.mkdir(parents=True, exist_ok=True)
    serial = out / f"serial-{args.mode}.log"
    sock = out / f"qmp-{args.mode}.sock"
    for p in (serial, sock):
        if p.exists():
            p.unlink()

    kvm = os.path.exists("/dev/kvm") and os.access("/dev/kvm", os.R_OK | os.W_OK)
    accel = "kvm" if kvm else "tcg,thread=multi"
    cmd = [
        "qemu-system-x86_64", "-machine", "q35", "-accel", accel, "-cpu", args.cpu,
        "-smp", str(args.smp), "-m", str(args.mem), "-display", "none", "-vga", "std",
        "-serial", f"file:{serial}", "-qmp", f"unix:{sock},server=on,wait=off",
        "-no-reboot", "-nic", "user,model=e1000", "-device", "virtio-rng-pci",
        "-cdrom", args.iso, "-boot", "order=d",
    ]
    if args.mode == "uefi":
        code, varsf = find_ovmf()
        vars_copy = out / f"OVMF_VARS-{args.mode}.fd"
        shutil.copy(varsf, vars_copy)
        cmd += [
            "-drive", f"if=pflash,format=raw,unit=0,readonly=on,file={code}",
            "-drive", f"if=pflash,format=raw,unit=1,file={vars_copy}",
        ]

    print("QEMU:", " ".join(cmd), flush=True)
    qlog = open(out / f"qemu-{args.mode}.log", "w")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=qlog, stderr=subprocess.STDOUT)
    qmp = Qmp(str(sock))

    marks = {}          # name -> {"wall_s": float, "line": str}
    seen_bytes = 0
    last_shot = -999.0
    last_hash = None
    shots = []
    done_at = None
    reason = "timeout"

    def screenshot(elapsed):
        nonlocal last_hash
        png = shots_dir / f"{args.mode}-{int(elapsed):04d}s.png"
        r = qmp.cmd("screendump", filename=str(png), format="png")
        if "error" in r:  # older QEMU: PPM only
            ppm = png.with_suffix(".ppm")
            qmp.cmd("screendump", filename=str(ppm))
            if shutil.which("convert") and ppm.exists():
                subprocess.run(["convert", str(ppm), str(png)], check=False)
                ppm.unlink()
        if png.exists():
            h = hashlib.sha1(png.read_bytes()).hexdigest()
            if h == last_hash:
                png.unlink()
            else:
                last_hash = h
                shots.append(png.name)

    try:
        while True:
            time.sleep(0.5)
            elapsed = time.time() - t0
            if proc.poll() is not None:
                reason = f"qemu exited ({proc.returncode})"
                break
            if elapsed > args.timeout:
                break

            # read newly written serial output
            if serial.exists():
                with open(serial, "rb") as f:
                    f.seek(seen_bytes)
                    chunk = f.read()
                    seen_bytes += len(chunk)
                for line in chunk.decode("utf-8", "replace").splitlines():
                    m = re.search(r"AVYX_MARK\s+(\S+)", line)
                    if m:
                        name = m.group(1).rstrip(":")
                        marks.setdefault(name, {"wall_s": round(elapsed, 1), "line": line.strip()})
                        print(f"[{elapsed:7.1f}s] {line.strip()}", flush=True)

            interval = 3 if elapsed < 90 else 15
            if elapsed - last_shot >= interval:
                screenshot(elapsed)
                last_shot = elapsed

            if "done" in marks and done_at is None:
                done_at = elapsed
            if "plasmashell_NOT_started" in marks and done_at is None:
                done_at = elapsed
            if done_at is not None and elapsed - done_at > 8:
                reason = "marker done"
                break
    finally:
        try:
            screenshot(time.time() - t0)
            qmp.cmd("quit")
        except Exception:
            pass
        try:
            proc.wait(timeout=15)
        except Exception:
            proc.kill()

    desktop = "plasmashell_started" in marks
    idle = marks.get("desktop_idle", {}).get("line", "")
    mem = re.search(r"mem_used_mb=(\d+) mem_total_mb=(\d+)", idle)
    result = {
        "mode": args.mode,
        "accel": "kvm" if kvm else "tcg (software emulation, timings are NOT representative)",
        "cpu_model": args.cpu,
        "vcpus": args.smp,
        "ram_mb": args.mem,
        "graphics": "QEMU std VGA, no 3D (software rendering in the guest)",
        "reason_stopped": reason,
        "reached_multi_user": "multi_user" in marks,
        "reached_desktop": desktop,
        "marks": marks,
        "idle_ram_used_mb": int(mem.group(1)) if mem else None,
        "screenshots": shots,
        "wall_seconds_total": round(time.time() - t0, 1),
    }
    (out / f"result-{args.mode}.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "marks"}, indent=2))
    sys.exit(0 if desktop else 1)


if __name__ == "__main__":
    main()
