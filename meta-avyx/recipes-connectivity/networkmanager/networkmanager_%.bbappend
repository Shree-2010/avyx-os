# Keep NetworkManager lean: Wi-Fi + Bluetooth tethering + nmcli, no vala/dnsmasq/ifupdown helpers.
PACKAGECONFIG = "readline nss nmcli systemd bluez5 wifi polkit"
