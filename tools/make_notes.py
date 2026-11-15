#!/usr/bin/env python3
"""Build release notes from MEASURED CI results only. Never writes a claim the tests did not show."""
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
version = sys.argv[2]
iso = next(out.glob("AVYX-OS-*.iso"), None)
size_mb = round(iso.stat().st_size / 1e6) if iso else None
sha = (out / (iso.name + ".sha256")).read_text().split()[0] if iso and (out / (iso.name + ".sha256")).exists() else "n/a"


def load(mode):
    p = out / f"result-{mode}.json"
    return json.loads(p.read_text()) if p.exists() else None


def mark(r, name):
    m = (r or {}).get("marks", {}).get(name)
    return f"{m['wall_s']} s" if m else "not reached"


lines = [f"# AVYX OS {version}", ""]
lines += [f"- ISO size: {size_mb} MB" if size_mb else "- ISO: missing", f"- SHA256: `{sha}`", ""]
lines += ["## Measured in CI (QEMU, 2 vCPU, 4 GB RAM, emulated Sandy Bridge CPU, std VGA = software rendering)", ""]
lines += ["| Check | UEFI | BIOS |", "|---|---|---|"]
u, b = load("uefi"), load("bios")


def cell(r, key):
    if not r:
        return "not run"
    v = r.get(key)
    return "PASS" if v else "FAIL"


lines += [
    f"| Boots to the system (multi-user) | {cell(u, 'reached_multi_user')} | {cell(b, 'reached_multi_user')} |",
    f"| Desktop shell started (plasmashell) | {cell(u, 'reached_desktop')} | {cell(b, 'reached_desktop')} |",
    f"| Seconds from power-on to multi-user (includes bootloader menu) | {mark(u, 'multi_user')} | {mark(b, 'multi_user')} |",
    f"| Seconds from power-on to desktop shell | {mark(u, 'plasmashell_started')} | {mark(b, 'plasmashell_started')} |",
    f"| RAM used at idle (MB, after 60 s settle) | {(u or {}).get('idle_ram_used_mb', 'n/a')} | {(b or {}).get('idle_ram_used_mb', 'n/a')} |",
    f"| Accelerator | {(u or {}).get('accel', 'n/a')} | {(b or {}).get('accel', 'n/a')} |",
    "",
]
dropped = out / "dropped-packages.txt"
if dropped.exists() and dropped.read_text().strip():
    lines += ["## Packages that were requested but do not exist in Debian trixie (not shipped)", "", "```", dropped.read_text().strip(), "```", ""]
lines += [
    "## Not verified in this build",
    "",
    "Everything not listed as PASS above was not tested: Wi-Fi/Bluetooth on real hardware, suspend/resume, hardware video decode,",
    "installation to disk with Calamares, Windows/Android app support, and behaviour on real old laptops.",
    "",
    "## Licensing",
    "",
    "AVYX-original code and art: MIT / CC0. All other software keeps its own license (see /usr/share/doc/*/copyright in the image).",
    "GPL source: the exact package list is in `packages.txt`; sources are available from the Debian archive (deb.debian.org / snapshot.debian.org).",
    "Based on Debian GNU/Linux; AVYX OS is not affiliated with or endorsed by the Debian project.",
]
print("\n".join(lines))
