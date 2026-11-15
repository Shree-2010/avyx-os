import QtQuick

Rectangle {
    id: root
    color: "#000000"
    property int stage

    Image {
        id: logo
        source: "images/logo.png"
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.4, 640)
        fillMode: Image.PreserveAspectFit
        opacity: 0
        NumberAnimation on opacity { to: 1; duration: 600; running: true }
    }

    Rectangle {
        id: track
        width: Math.max(parent.width * 0.3, 240)
        height: 3
        radius: 2
        color: "#22ffffff"
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * 0.9
        Rectangle {
            height: parent.height
            radius: 2
            color: "#cde1ff"
            width: parent.width * Math.min(root.stage / 6, 1)
            Behavior on width { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
        }
    }
}
