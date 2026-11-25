# AVYX OS — BUILD BEYOND LIMITS

AVYX OS is a Yocto-built Linux distribution with a Wayland desktop (labwc compositor + the AVYX GTK4/Python shell).

- `meta-avyx/` — Yocto layer (distro `avyx`, machine `avyx-x86-64`, kernel, images, desktop recipes)
- `yocto/` — pinned layer list, setup script, build configuration templates
- `src/` — AVYX desktop source (shell, apps, assets)
- `tools/` — asset generators and CI test tooling
- `.github/workflows/` — CI: Yocto build, boot tests in QEMU (UEFI + BIOS), UI preview

Build locally (needs a normal Yocto host):

    yocto/setup.sh
    source yocto/sources/poky/oe-init-build-env yocto/build
    bitbake avyx-image

The result is a hybrid BIOS/UEFI live ISO in `yocto/build/tmp/deploy/images/avyx-x86-64/`.

Earlier experiments with a Debian/KDE base are kept on the `archive-debian-kde` branch only; the product is Yocto-only.

Licenses: AVYX code is MIT. Third-party components keep their own licenses (see the license manifest inside the image).
