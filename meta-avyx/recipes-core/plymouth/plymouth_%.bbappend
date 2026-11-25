# AVYX: only the script theme engine (our theme) plus text/details fallbacks; no dracut initrd helper.
PLYMOUTH_THEMES = "script text details"
PACKAGECONFIG:remove = "initrd"
PLYMOUTH_BACKGROUND_COLOR = "0x000000"
PLYMOUTH_BACKGROUND_START_COLOR_STOP = "0x000000"
PLYMOUTH_BACKGROUND_END_COLOR_STOP = "0x000000"
