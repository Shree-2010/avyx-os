// AVYX desktop layout, applied once per user by /usr/local/lib/avyx/apply-layout.sh.
// Slim top bar (global menu | flexible gap for the activity pill | tray | clock) and a floating,
// centred, icon-only dock at the bottom. New panels are created first and the old ones removed
// last, so an error half-way can never leave the desktop without a panel.
var oldPanels = panels();

var bar = new Panel();
bar.location = "top";
bar.height = 30;
bar.floating = false;
bar.hiding = "none";
var menu = bar.addWidget("org.kde.plasma.kickoff");
menu.currentConfigGroup = ["General"];
menu.writeConfig("icon", "avyx-menu");
bar.addWidget("org.kde.plasma.appmenu");
bar.addWidget("org.kde.plasma.panelspacer");
bar.addWidget("org.kde.plasma.panelspacer");
bar.addWidget("org.kde.plasma.systemtray");
bar.addWidget("org.kde.plasma.digitalclock");

var dock = new Panel();
dock.location = "bottom";
dock.height = 64;
dock.floating = true;
dock.lengthMode = "fit";
dock.alignment = "center";
dock.hiding = "dodgewindows";
var tasks = dock.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers",
    "applications:org.kde.dolphin.desktop," +
    "applications:org.kde.konsole.desktop," +
    "applications:org.kde.kate.desktop," +
    "applications:org.kde.gwenview.desktop," +
    "applications:systemsettings.desktop," +
    "applications:avyx-installer.desktop");
tasks.writeConfig("iconSpacing", "2");
tasks.writeConfig("maxStripes", "1");
dock.addWidget("org.kde.plasma.marginsseparator");
dock.addWidget("org.kde.plasma.trash");

// Glass: translucent panels (the compositor blurs what is behind them). Guarded so a Plasma
// version without this property can never abort the layout.
[bar, dock].forEach(function (p) {
    try { p.opacity = "translucent"; } catch (e) {}
});

for (var i = 0; i < oldPanels.length; i++) {
    oldPanels[i].remove();
}
