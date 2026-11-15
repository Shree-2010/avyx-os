import QtQuick
import calamares.slideshow 1.0

Presentation {
    id: presentation
    Slide {
        Rectangle { anchors.fill: parent; color: "#000000" }
        Image {
            source: "logo.png"
            anchors.centerIn: parent
            width: Math.min(parent.width * 0.5, 420)
            fillMode: Image.PreserveAspectFit
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 40
            text: "BUILD BEYOND LIMITS"
            color: "#a9b3cc"
            font.pixelSize: 16
            font.letterSpacing: 4
        }
    }
}
