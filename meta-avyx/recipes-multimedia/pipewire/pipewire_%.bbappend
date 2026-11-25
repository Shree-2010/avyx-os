# Desktop audio only: ALSA + Bluetooth + PulseAudio protocol server + WirePlumber. No ffmpeg/gstreamer/jack/camera.
PACKAGECONFIG:class-target = " \
    alsa pipewire-alsa bluez systemd systemd-system-service systemd-user-service \
    ${PIPEWIRE_SESSION_MANAGER} udev volume pw-cat readline gsettings \
"
