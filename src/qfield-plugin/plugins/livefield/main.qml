import QtQuick
import QtQuick.Controls
import QtWebSockets

import org.qfield
import org.qgis
import Theme

import "qrc:/qml" as QFieldItems

Item {
  id: plugin

  property var mainWindow: iface.mainWindow()
  property var mapCanvas: iface.mapCanvas()
  property var positionSource: iface.findItemByObjectName('positionSource')
  property ProjectInfo projectInfo: iface.findItemByObjectName("projectInfo")
  property QFieldCloudProjectsModel cloudProjectsModel: iface.findItemByObjectName("cloudProjectsModel")

  readonly property string serverUrl: "wss://live.field.hotosm.org"
  property string userName: projectInfo && projectInfo.cloudUserInformation ? (projectInfo.cloudUserInformation.username || "") : ""
  property string groupToken: cloudProjectsModel && cloudProjectsModel.currentProject ? (cloudProjectsModel.currentProject.owner + "/" + cloudProjectsModel.currentProject.name) : ""

  function tryAutoConnect() {
    if (ws.active || ws.status === WebSocket.Open) {
      return
    }
    if (!userName || !groupToken) {
      return
    }
    ws.url = serverUrl
    ws.active = true
  }

  onUserNameChanged: tryAutoConnect()
  onGroupTokenChanged: tryAutoConnect()

  Component.onCompleted: {
    iface.addItemToPluginsToolbar(pluginButton)
    tryAutoConnect()
  }

  Connections {
    target: positionSource

    property real lastPush: 0
    function onPositionInformationChanged() {
      if (ws.status == WebSocket.Open && Date.now() - lastPush > 1000) {
        ws.sendPosition()
        lastPush = Date.now()
      }
    }
  }

  ListModel {
    id: devicesModel
  }

  Repeater {
    parent: mapCanvas

    model: devicesModel

    QFieldItems.LocationMarker {
      visible: deviceKey != ws.deviceKey && lon != "NaN" && lat != "NaN"

      mapSettings: mapCanvas.mapSettings

      color: userColor

      location: GeometryUtils.reprojectPoint(GeometryUtils.point(lon, lat), CoordinateReferenceSystemUtils.wgs84Crs(), mapCanvas.mapSettings.destinationCrs)
      direction: deviceDirection !== "NaN" ? deviceDirection : -1
      speed: deviceSpeed !== "NaN" ? deviceSpeed : -1
    }
  }

  Dialog {
    id: detailsDialog
    title: qsTr("Details")
    focus: true
    font: Theme.defaultFont
    parent: mainWindow.contentItem

    x: (mainWindow.width - width) / 2
    y: (mainWindow.height - height - 80) / 2

    Column {
      width: Math.min(mainWindow.width - 60, 400)
      height: childrenRect.height
      spacing: 10

      Row {
        width: parent.width
        spacing: 10

        Label {
          anchors.verticalCenter: parent.verticalCenter
          width: parent.width - 58
          font: Theme.defaultFont
          color: Theme.mainTextColor
          wrapMode: Text.WordWrap
          text: "Group: <b>" + ws.groupKey + "</b>"
        }

        QfToolButton {
          round: true
          iconSource: Theme.getThemeVectorIcon("ic_copy_black_24dp")
          iconColor: Theme.mainTextColor
          bgcolor: "transparent"

          onClicked: {
            platformUtilities.copyTextToClipboard(ws.groupKey)
          }
        }
      }

      ScrollView {
        leftPadding: 0
        rightPadding: 0
        topPadding: 0
        bottomPadding: 0
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: QfScrollBar {
        }
        width: parent.width
        height: Math.min(devicesContainer.height, (mainWindow.height - 200) / 2)
        contentWidth: parent.width
        contentHeight: devicesContainer.height
        clip: true

        Column {
          id: devicesContainer
          width: parent.width
          height: childrenRect.height
          spacing: 5

          Repeater {
            id: devicesRepeater
            model: devicesModel

            width: parent.width

            Row {
              width: parent.width
              spacing: 10

              Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                color: userColor
                width: 24
                height: 24
                radius: width / 2
              }

              Label {
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width - 92
                font: Theme.defaultFont
                color: Theme.mainTextColor
                wrapMode: Text.WordWrap
                text: userName
              }

              QfToolButton {
                width: 48
                height: 48
                enabled: lon != "NaN" && lat != "NaN"
                iconSource: Theme.getThemeVectorIcon("ic_view_black_24dp")
                iconColor: enabled ? Theme.mainTextColor : Theme.mainTextDisabledColor

                onClicked: {
                  let point = GeometryUtils.reprojectPoint(GeometryUtils.point(lon, lat), CoordinateReferenceSystemUtils.wgs84Crs(), mapCanvas.mapSettings.destinationCrs)
                  mapCanvas.mapSettings.center = point
                }
              }
            }
          }
        }
      }

      Row {
        width: parent.width
        spacing: 10

        QfTextField {
          id: messageInput
          anchors.verticalCenter: parent.verticalCenter
          width: parent.width - 58
          font: Theme.defaultFont
          placeholderText: "Broadcast message content"
        }

        QfToolButton {
          round: true
          iconSource: "send.svg"
          iconColor: Theme.mainTextColor
          bgcolor: "transparent"

          onClicked: {
            let messageContent = messageInput.text.trim().replace(/\"/g, "'")
            if (messageContent !== '') {
              let message =  "{\"type\": \"message\"" +
                  ", \"content\": \"" + messageContent + "\"" +
                  "}"
              ws.sendTextMessage(message)
            }
          }
        }
      }
    }

    standardButtons: Dialog.Ok | Dialog.Close
    onAccepted: {
      ws.active = false
      devicesModel.clear()
    }

    Component.onCompleted: {
      standardButton(Dialog.Ok).text = "Disconnect"
    }
  }

  WebSocket {
    id: ws
    active: false
    url: plugin.serverUrl

    property string groupKey: ''
    property string deviceKey: ''

    function sendPosition() {
      let message = "{\"type\": \"position\"" +
          ", \"lat\": \"" + positionSource.positionInformation.latitude + "\"" +
          ", \"lon\": \"" + positionSource.positionInformation.longitude + "\"" +
          ", \"speed\": \"" + positionSource.positionInformation.speed + "\"" +
          ", \"dir\": \"" + positionSource.positionInformation.direction + "\"" +
          "}"
      ws.sendTextMessage(message)
    }

    onErrorStringChanged: {
      if (errorString !== '') {
        mainWindow.displayToast('WebSocket error: ' + errorString)
      }
    }

    onStatusChanged: (status) => {
                       if (status === WebSocket.Open) {
                         sendTextMessage("{\"type\": \"join\", \"user\": \"" + plugin.userName + "\", \"group\": \"" + plugin.groupToken + "\"}")
                         sendPosition()
                       }
                     }

    onTextMessageReceived: (message) => {
                             let event = JSON.parse(message);
                             if (event["type"] === "created" || event["type"] === "joined") {
                               groupKey = event["group"]
                               deviceKey = event["device"]

                               sendPosition();
                             } else if (event["type"] === "message") {
                               let devicesCount = devicesModel.count
                               for (let i = 0; i < devicesCount; i++) {
                                 let item = devicesModel.get(i)
                                 if (item.deviceKey === event["device"]) {
                                   mainWindow.displayToast(item.userName + ": " + event["content"])
                                   platformUtilities.vibrate(500)
                                 }
                               }
                             } else if (event["type"] === "positions") {
                               let devicesHandled = []
                               let devicesGone = 0

                               let devicesCount = devicesModel.count
                               for (let i = 0; i < devicesCount; i++) {
                                 let item = devicesModel.get(i - devicesGone)
                                  if (event["devices"][item.deviceKey] !== undefined) {
                                    devicesHandled.push(item.deviceKey)
                                    item.lat = event["devices"][item.deviceKey]["lat"]
                                    item.lon = event["devices"][item.deviceKey]["lon"]
                                    item.deviceSpeed = event["devices"][item.deviceKey]["speed"]
                                    item.deviceDirection = event["devices"][item.deviceKey]["dir"]
                                  } else {
                                    devicesModel.remove(i)
                                    devicesGone++
                                  }
                               }

                               for (let dK in event["devices"]) {
                                 if (devicesHandled.indexOf(dK) == -1) {
                                   devicesModel.append({ "deviceKey": dK,
                                                         "userName": event["devices"][dK]["user_name"],
                                                         "userColor": event["devices"][dK]["user_color"],
                                                         "lat": event["devices"][dK]["lat"],
                                                         "lon": event["devices"][dK]["lon"],
                                                         "deviceSpeed": event["devices"][dK]["speed"],
                                                         "deviceDirection": event["devices"][dK]["dir"],
                                                       })
                                 }
                               }
                             }
                           }
  }

  QfToolButton {
    id: pluginButton
    iconSource: 'icon.svg'
    iconColor: ws.status == WebSocket.Open ? Theme.mainColor : "white"
    bgcolor: Theme.darkGray
    round: true

    onClicked: {
      if (ws.status == WebSocket.Open) {
        detailsDialog.open()
      } else {
        plugin.tryAutoConnect()
        if (!plugin.userName || !plugin.groupToken) {
          mainWindow.displayToast(qsTr("LiveField: waiting for QFieldCloud project to load"))
        }
      }
    }
  }
}
