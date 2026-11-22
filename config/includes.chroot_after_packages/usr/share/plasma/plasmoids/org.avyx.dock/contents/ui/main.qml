// AVYX Dock: pinned apps + running windows in one row, icons swell smoothly under the pointer.
// Pure QML on top of Plasma's own task model, so launching, activating and minimizing behave
// exactly like the stock task manager.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager

PlasmoidItem {
    id: root

    preferredRepresentation: fullRepresentation

    TaskManager.TasksModel {
        id: tasksModel
        groupMode: TaskManager.TasksModel.GroupApplications
        sortMode: TaskManager.TasksModel.SortManual
        separateLaunchers: false
        launcherList: Plasmoid.configuration.launchers
        onLauncherListChanged: {
            if (launcherList.join(",") !== Plasmoid.configuration.launchers.join(",")) {
                Plasmoid.configuration.launchers = launcherList;
            }
        }
    }

    function activateRow(row, isWindow) {
        var idx = tasksModel.makeModelIndex(row);
        if (isWindow) {
            tasksModel.requestActivate(idx);
        } else {
            tasksModel.requestNewInstance(idx);
        }
    }

    fullRepresentation: Item {
        id: dock

        readonly property real baseSize: 40
        readonly property real gap: 8
        readonly property real maxScale: 1.35
        readonly property int count: tasksModel.count
        readonly property real restWidth: count * baseSize + Math.max(0, count - 1) * gap
        readonly property real headroom: baseSize * 1.3

        property real pointerX: -10000
        property real amount: 0

        Layout.minimumWidth: restWidth + headroom
        Layout.preferredWidth: restWidth + headroom
        Layout.minimumHeight: baseSize * maxScale + 4
        Layout.preferredHeight: baseSize * maxScale + 4

        Behavior on amount { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }

        function bump(index) {
            var center = (width - restWidth) / 2 + index * (baseSize + gap) + baseSize / 2;
            var d = Math.abs(pointerX - center) / (2.4 * (baseSize + gap));
            return d >= 1 ? 0 : 0.5 * (1 + Math.cos(Math.PI * d));
        }
        function scaleOf(index) {
            return 1 + (maxScale - 1) * amount * bump(index);
        }
        function leftOf(index) {
            var total = 0;
            for (var i = 0; i < count; i++) {
                total += baseSize * scaleOf(i) + (i > 0 ? gap : 0);
            }
            var x = (width - total) / 2;
            for (var j = 0; j < index; j++) {
                x += baseSize * scaleOf(j) + gap;
            }
            return x;
        }

        QQC2.Menu {
            id: ctx
            property int row: -1
            property bool isWindow: false
            property bool pinned: false
            property url launcherUrl
            popupType: QQC2.Popup.Window
            QQC2.MenuItem {
                text: ctx.isWindow ? "Show" : "Open"
                onTriggered: root.activateRow(ctx.row, ctx.isWindow)
            }
            QQC2.MenuItem {
                text: "New Window"
                onTriggered: tasksModel.requestNewInstance(tasksModel.makeModelIndex(ctx.row))
            }
            QQC2.MenuItem {
                text: ctx.pinned ? "Remove from Dock" : "Keep in Dock"
                onTriggered: {
                    if (ctx.pinned) {
                        tasksModel.requestRemoveLauncher(ctx.launcherUrl);
                    } else {
                        tasksModel.requestAddLauncher(ctx.launcherUrl);
                    }
                }
            }
            QQC2.MenuItem {
                text: "Quit"
                enabled: ctx.isWindow
                onTriggered: tasksModel.requestClose(tasksModel.makeModelIndex(ctx.row))
            }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
            onPositionChanged: mouse => { dock.pointerX = mouse.x; dock.amount = 1; }
            onEntered: dock.amount = 1
            onExited: dock.amount = 0
        }

        Repeater {
            model: tasksModel
            delegate: Item {
                id: slot
                required property int index
                required property var model

                readonly property real s: dock.scaleOf(index)
                readonly property bool running: slot.model.IsWindow === true
                property real lift: 0
                property bool launching: false
                width: dock.baseSize * s
                height: dock.baseSize * s
                x: dock.leftOf(index)
                y: dock.height - height - 4 - lift
                onRunningChanged: if (running) launching = false

                Timer { interval: 8000; running: slot.launching; onTriggered: slot.launching = false }
                SequentialAnimation {
                    running: slot.launching
                    loops: Animation.Infinite
                    NumberAnimation { target: slot; property: "lift"; to: 16; duration: 280; easing.type: Easing.OutQuad }
                    NumberAnimation { target: slot; property: "lift"; to: 0; duration: 280; easing.type: Easing.InQuad }
                    onRunningChanged: if (!running) slot.lift = 0
                }

                Kirigami.Icon {
                    anchors.fill: parent
                    source: slot.model.decoration
                    active: click.containsMouse
                    smooth: true
                }
                // running indicator
                Rectangle {
                    visible: slot.model.IsWindow === true
                    width: 5; height: 5; radius: 2.5
                    color: slot.model.IsActive === true ? "#ffffff" : "#9aa3c4"
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.bottom
                    anchors.topMargin: 1
                }
                MouseArea {
                    id: click
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onClicked: mouse => {
                        if (mouse.button === Qt.RightButton) {
                            ctx.row = slot.index;
                            ctx.isWindow = slot.running;
                            ctx.launcherUrl = slot.model.LauncherUrlWithoutIcon;
                            ctx.pinned = tasksModel.launcherPosition(slot.model.LauncherUrlWithoutIcon) !== -1;
                            ctx.popup();
                            return;
                        }
                        if (!slot.running) slot.launching = true;
                        root.activateRow(slot.index, slot.running);
                    }
                }
                QQC2.ToolTip {
                    visible: click.containsMouse && !ctx.visible
                    delay: 400
                    text: slot.model.display
                }
            }
        }
    }
}
