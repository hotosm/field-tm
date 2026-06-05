import QtQuick
import org.qfield
import org.qgis
import Theme

Item {
  id: plugin

  property var mainWindow: iface.mainWindow()

  // ── Cycle to next map theme ──
  function cycleTheme() {
    var names = qgisProject.mapThemeCollection.mapThemes
    if (!names || names.length < 2) {
      mainWindow.displayToast(qsTr("Next Theme: project needs at least 2 map themes"))
      return
    }

    var current = flatLayerTree.mapTheme
    var idx = names.indexOf(current)
    var next = names[(idx + 1) % names.length]
    flatLayerTree.mapTheme = next
    mainWindow.displayToast(next)
  }

  // ── Toolbar button ──
  QfToolButton {
    id: nextThemeBtn
    round: true
    iconSource: Qt.resolvedUrl("basemap.svg")
    iconColor: "#4CAF50"
    bgcolor: "#FFFFFF"
    onClicked: plugin.cycleTheme()
  }

  Component.onCompleted: {
    iface.addItemToPluginsToolbar(nextThemeBtn)
  }
}
