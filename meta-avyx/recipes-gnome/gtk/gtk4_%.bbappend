# No GStreamer media backend inside GTK (AVYX uses its own media player process); saves a large build.
PACKAGECONFIG:remove = "gstreamer"
