// AVYX Dock: pinned apps + running windows in one row, icons swell smoothly under the pointer.
// Pure QML on top of Plasma's own task model, so launching, activating and minimizing behave
// exactly like the stock task manager.
import QtQuick
import QtQuick.Layouts
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
    }

    fullRepresentation: Item {
        id: dock

        readonly property real baseSize: 40
        readonly property real gap: 8
        readonly property real maxScale: 1.45
        readonly property int count: tasksModel.count
        readonly property real restWidth: count * baseSize + Math.max(0, count - 1) * gap
        readonly property real headroom: baseSize * 1.3

        property real pointerX: -10000
        property real amount: 0

        Layout.minimumWidth: restWidth + headroom
        Layout.preferredWidth: restWidth + headroom
        Layout.minimumHeight: baseSize * maxScale + 8
        Layout.preferredHeight: baseSize * maxScale + 8

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
                width: dock.baseSize * s
                height: dock.baseSize * s
                x: dock.leftOf(index)
                y: dock.height - height - 6

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
                    onClicked: {
                        var idx = tasksModel.makeModelIndex(slot.index);
                        if (slot.model.IsWindow === true) {
                            tasksModel.requestActivate(idx);
                        } else {
                            tasksModel.requestNewInstance(idx);
                        }
                    }
                }
            }
        }
    }
}
