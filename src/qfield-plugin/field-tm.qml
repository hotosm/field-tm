pragma Translator: FieldTM

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Particles
import QtQuick.Shapes

import org.qfield
import org.qgis
import Theme

Item {
  id: fieldTM

  property var mainWindow: iface.mainWindow()
  property var featureListForm: iface.findItemByObjectName("featureForm")
  property var mapCanvas: iface.mapCanvas()
  property var mapCanvasContainer: iface.findItemByObjectName("mapCanvasContainer")
  property var busyOverlay: iface.findItemByObjectName("busyOverlay")

  property var qfieldSettings: iface.findItemByObjectName("qfieldSettings")
  property ProjectInfo projectInfo: iface.findItemByObjectName("projectInfo")

  property QFieldCloudConnection cloudConnection: iface.findItemByObjectName("cloudConnection")
  property QFieldCloudProjectsModel cloudProjectsModel: iface.findItemByObjectName("cloudProjectsModel")

  property bool outdated: false
  property bool reader: false
  property bool singleTaskMode: false

  property string currentUser: ""
  property var currentTask: undefined
  property bool currentTaskHasAddedFeature: false
  property var myTaskIds: []
  property var pendingTask: undefined

  property var tasksLayer: qgisProject.mapLayersByName("tasks")[0];
  property var surveyLayer: qgisProject.mapLayersByName("survey")[0];

  property string mainColor: "#d73f3f"

  // Skip-list uuids match what QField's PluginManager would assign if the user
  // installed the upstream version, so we don't create duplicate toolbar buttons.
  property var _companionPlugins: [
    {
      "uuid": "livefield",
      "source": Qt.resolvedUrl("./plugins/livefield/main.qml")
    },
    {
      "uuid": "qfield-next-theme-plugin",
      "source": Qt.resolvedUrl("./plugins/next-theme/main.qml")
    }
  ]
  property var _companionInstances: []

  Rectangle {
    id: fieldTMContainer
    parent: mapCanvasContainer
    anchors {
      top: parent.top
      left: parent.left
      right: parent.right
      topMargin: mainWindow.sceneTopMargin + 56
      leftMargin: mainWindow.sceneLeftMargin + 56
      rightMargin: mainWindow.sceneRightMargin + 56
    }

    Rectangle {
      id: informationContainer
      anchors {
        top: parent.top
        left: parent.left
        right: parent.right
        topMargin: 24
      }

      height: fieldTM.currentTask === undefined ? informationLayout.childrenRect.height + 48 : 0
      Behavior on height {
        PropertyAnimation {
          duration: 250
          easing.type: Easing.OutQuart
        }
      }

      gradient: Gradient {
        GradientStop { position: 0.0; color: "#fdebef" }
        GradientStop { position: 1.0; color: "#ffffff" }
      }
      border.width: 1
      border.color: "#fdcfd6"
      radius: 12
      clip: true

      ColumnLayout {
        id: informationLayout
        anchors {
          top: parent.top
          left: parent.left
          right: parent.right
          topMargin: 38
          leftMargin: 12
          rightMargin: 12
        }

        Text {
          Layout.fillWidth: true
          font: Theme.tipFont
          color: "#222222"
          wrapMode: Text.WordWrap

          text: fieldTM.reader ? qsTranslate("FieldTM", "Tap on an available task area on the map to view surveys.") : qsTranslate("FieldTM", "Tap on an available task area on the map to start surveying.")
        }

        Text {
          Layout.fillWidth: true
          Layout.preferredHeight: text !== "" ? contentHeight : 0
          font: Theme.tipFont
          color: "#222222"
          wrapMode: Text.WordWrap
          linkColor: fieldTM.mainColor

          text: fieldTM.myTaskIds.length > 0 ? `<a href=\"#mytasks\">${qsTranslate("FieldTM", "Your tasks: %1").arg(fieldTM.myTaskIds.map(id => "#" + id).join(", "))}</a>` : ""

          onLinkActivated: (link) => {
            if (link === "#mytasks") {
              zoomToMyTasks();
            }
          }
        }

        Text {
          Layout.fillWidth: true
          Layout.preferredHeight: text !== "" ? contentHeight : 0
          font: Theme.tipFont
          color: "#f67c0f"
          wrapMode: Text.WordWrap

          text: fieldTM.outdated ? qsTranslate("FieldTM", "Data sync occurred over half an hour ago, synchronizing is recommended.") : ""
        }

        Text {
          Layout.fillWidth: true
          Layout.preferredHeight: text !== "" ? contentHeight : 0
          font: Theme.tipFont
          color: "#99222222"
          wrapMode: Text.WordWrap
          linkColor: fieldTM.mainColor

          text: fieldTM.cloudConnection.hasToken && fieldTM.cloudConnection.isReachable ? `<a href=\"#synchronize\">${qsTranslate("FieldTM", "Synchronize tasks")}</a>` : ""

          onLinkActivated: (link) => {
            if (link === "#synchronize") {
              fieldTM.busyOverlay.text = qsTranslate("FieldTM", "Synchronizing tasks");
              fieldTM.busyOverlay.showProgress = false;
              fieldTM.busyOverlay.state = "visible";
              synchronizeCloud();
            }
          }
        }
      }
    }

    Rectangle {
      id: taskInfoContainer
      anchors {
        top: parent.top
        left: parent.left
        right: parent.right
        topMargin: 24
      }

      height: taskInfoText.text !== "" ? taskInfoText.contentHeight + 48 : 0
      Behavior on height {
        PropertyAnimation {
          duration: 250
          easing.type: Easing.OutQuart
        }
      }

      color: "#ffffff"
      border.width: 1
      border.color: "#fdcfd6"
      radius: 12
      clip: true

      Text {
        id: taskInfoText
        anchors {
          top: parent.top
          left: parent.left
          right: parent.right
          topMargin: 36
          leftMargin: 12
          rightMargin: 12
        }
        font: Theme.tipFont
        color: "#222222"
        wrapMode: Text.WordWrap
        textFormat: Text.PlainText

        text: fieldTM.currentTask !== undefined ? taskInfoSummary(fieldTM.currentTask) : ""
      }
    }

    Rectangle {
      anchors {
        top: parent.top
        left: parent.left
        right: parent.right
      }
      height: 48
      radius: 24
      color: Theme.toolButtonBackgroundColor

      Item {
        anchors.centerIn: parent
        implicitWidth: 60
        implicitHeight: 36
        transform: [Scale { xScale: 0.75; yScale: 0.75 }]

        Shape {
          ShapePath {
            strokeColor: "transparent"
            fillColor: fieldTM.mainColor
            PathSvg { path: "M 37.0266 20.775 C 37.0266 20.291 37.1298 19.859 37.3362 19.4862 C 37.541 19.1118 37.813 18.807 38.1506 18.5638 C 38.4866 18.3214 38.865 18.1374 39.2858 18.0134 C 39.705 17.8902 40.1274 17.8278 40.5538 17.8278 C 40.9786 17.8278 41.4026 17.8902 41.8234 18.0134 C 42.2418 18.1374 42.6202 18.3214 42.9562 18.5638 C 43.2946 18.807 43.5658 19.1118 43.7722 19.4862 C 43.9786 19.859 44.081 20.291 44.081 20.775 L 44.081 27.147 C 44.081 27.6414 43.9786 28.075 43.7722 28.4422 C 43.5658 28.811 43.2946 29.1142 42.9562 29.3574 C 42.6202 29.6014 42.2418 29.7862 41.8234 29.9086 C 41.4026 30.0318 40.9786 30.0934 40.5538 30.0934 C 40.1274 30.0934 39.705 30.0318 39.2858 29.9086 C 38.865 29.7862 38.4866 29.6014 38.1506 29.3574 C 37.813 29.1142 37.541 28.811 37.3362 28.4422 C 37.1298 28.075 37.0266 27.6414 37.0266 27.147 L 37.0266 20.775 M 39.0514 27.1502 C 39.0514 27.5654 39.2826 27.875 39.5658 28.0718 C 39.8474 28.2702 40.181 28.375 40.5658 28.375 C 40.949 28.375 41.2842 28.2702 41.5666 28.0718 C 41.8474 27.875 42.0082 27.5654 42.0082 27.1502 L 42.0082 20.7782 C 42.0082 20.3614 41.8474 20.0526 41.5666 19.8558 C 41.2842 19.6582 40.949 19.5254 40.5658 19.5254 C 40.181 19.5254 39.8474 19.6582 39.5658 19.8558 C 39.2826 20.0526 39.0514 20.3614 39.0514 20.7782 L 39.0514 27.1502 " }
          }
          ShapePath {
            strokeColor: "transparent"
            fillColor: fieldTM.mainColor
            PathSvg { path: "M 33.379 17.815 L 33.379 22.99 L 30.152 22.99 L 30.152 17.815 L 28.387 17.815 L 28.387 30.1 L 30.152 30.1 L 30.152 24.923 L 33.379 24.923 L 33.379 30.1 L 35.278 30.1 L 35.278 17.815 L 33.379 17.815 " }
          }
          ShapePath {
            strokeColor: "transparent"
            fillColor: fieldTM.mainColor
            PathSvg { path: "M 52.431 17.815 L 45.426 17.815 L 45.426 19.622 L 48.015 19.622 L 47.985 30.1 L 49.847 30.1 L 49.847 19.622 L 52.431 19.622 L 52.431 17.815 " }
          }
          ShapePath {
            strokeColor: "transparent"
            fillColor: fieldTM.mainColor
            PathSvg { path: "M 65.4234 28.7668 L 79.6794 28.7668 L 71.1554 19.1684 L 62.669 9.57 L 54.181 0.0004 L 11.5394 0.0004 L 20.0258 9.57 L 5.73784 9.57 L 14.2258 19.1684 L 14.2914 19.2332 L 0.00024 19.2332 L 8.52184 28.8316 L 17.013 38.43 L 25.5002 48.0004 L 68.1418 48.0004 L 59.6506 38.43 L 59.5882 38.3364 L 73.8786 38.3364 L 65.4234 28.7668 M 39.8394 39.9492 C 30.3186 39.9492 22.601 32.8084 22.601 24.0012 C 22.601 15.1908 30.3186 8.05 39.8394 8.05 C 49.361 8.05 57.0794 15.1908 57.0794 24.0012 C 57.0794 32.8084 49.361 39.9492 39.8394 39.9492 " }
          }
        }
      }

      RowLayout {
        width: parent.width
        height: parent.height
        spacing: 8

        QfToolButton {
          id: releaseButton
          round: true

          iconSource: Theme.getThemeVectorIcon("ic_arrow_left_white_24dp")
          iconColor: "#000000"
          bgcolor: "#ffffff"
          padding: 0

          Layout.preferredWidth: 36
          Layout.preferredHeight: 36
          Layout.leftMargin: 8
          Layout.alignment: Qt.AlignVCenter
          visible: fieldTM.currentTask !== undefined && !fieldTM.singleTaskMode

          onClicked: {
            if (fieldTM.currentTask !== undefined) {
              const taskId = fieldTM.currentTask.attribute("task_id");
              if (!fieldTM.reader && isAssignedToMe(fieldTM.currentTask)) {
                releaseTask(fieldTM.currentTask);
                mainWindow.displayToast(qsTranslate("FieldTM", "Released task #%1").arg(taskId));
              } else {
                mainWindow.displayToast(qsTranslate("FieldTM", "Leaving task #%1").arg(taskId));
              }
              fieldTM.currentTask = undefined;
            }
          }
        }

        QfToolButton {
          id: completeButton
          round: true

          iconSource: Theme.getThemeVectorIcon("ic_check_white_24dp")
          iconColor: "#000000"
          bgcolor: "#ffffff"
          padding: 0

          Layout.preferredWidth: 36
          Layout.preferredHeight: 36
          Layout.alignment: Qt.AlignVCenter
          visible: fieldTM.currentTask !== undefined && (fieldTM.currentTaskHasAddedFeature || fieldTM.currentTask.attribute("status") === "completed")

          onClicked: {
            if (fieldTM.currentTask !== undefined) {
              if (!fieldTM.reader) {
                setTaskAttributes(fieldTM.currentTask, { "status": "completed" });

                mainWindow.displayToast(qsTranslate("FieldTM", "Marked task #%1 as completed").arg(fieldTM.currentTask.attribute("task_id")));
                rewardEmitter.reward();
              }

              if (!fieldTM.singleTaskMode) {
                fieldTM.currentTask = undefined;
              }
            }
          }
        }

        Item {
          Layout.fillWidth: true
        }

        QfToolButton {
          id: openFeaturesButton
          round: true

          iconSource: Theme.getThemeVectorIcon("ic_list_black_24dp")
          iconColor: "#000000"
          bgcolor: "#ffffff"
          padding: 0

          Layout.preferredWidth: 36
          Layout.preferredHeight: 36
          Layout.alignment: Qt.AlignVCenter
          visible: fieldTM.currentTask !== undefined

          onClicked: {
            fieldTM.featureListForm.model.setFeatures(fieldTM.surveyLayer, taskIntersectsExpression(fieldTM.currentTask));
            featureListForm.extentController.zoomToAllFeatures();
          }
        }

        QfToolButton {
          id: zoomToButton
          round: true

          iconSource: Theme.getThemeVectorIcon("zoom_out_map_24dp")
          iconColor: "#000000"
          bgcolor: "#ffffff"
          padding: 0

          Layout.preferredWidth: 36
          Layout.preferredHeight: 36
          Layout.rightMargin: 8
          Layout.alignment: Qt.AlignVCenter

          onClicked: {
            if (fieldTM.currentTask !== undefined) {
              const rectangle = GeometryUtils.reprojectRectangle(GeometryUtils.boundingBox(fieldTM.currentTask.geometry), fieldTM.tasksLayer.crs, mapCanvas.mapSettings.destinationCrs);
              mapCanvas.mapSettings.setExtent(rectangle, true);
            } else {
              mapCanvas.mapSettings.setCenterToLayer(fieldTM.tasksLayer, true);
            }
          }
        }
      }
    }
  }

  Dialog {
    id: takeoverDialog
    parent: mainWindow.contentItem
    modal: true
    font: Theme.defaultFont
    title: qsTranslate("FieldTM", "Task already assigned")

    property string assignee: ""

    x: (mainWindow.width - width) / 2
    y: (mainWindow.height - height - 80) / 2

    Label {
      width: Math.min(mainWindow.width - 60, 400)
      font: Theme.defaultFont
      color: Theme.mainTextColor
      wrapMode: Text.WordWrap
      textFormat: Text.PlainText
      text: fieldTM.pendingTask !== undefined ? qsTranslate("FieldTM", "Task #%1 is assigned to %2. Enter it anyway? It will stay assigned to them.").arg(taskAttribute(fieldTM.pendingTask, "task_id")).arg(takeoverDialog.assignee) : ""
    }

    standardButtons: Dialog.Ok | Dialog.Cancel

    onAccepted: {
      if (fieldTM.pendingTask !== undefined) {
        enterTask(fieldTM.pendingTask, false);
      }
      fieldTM.pendingTask = undefined;
    }
    onRejected: {
      fieldTM.pendingTask = undefined;
    }
  }

  ParticleSystem {
    id: rewardSystem
    parent: mapCanvasContainer
  }

  Emitter {
    id: rewardEmitter
    enabled: false
    parent: mapCanvasContainer
    anchors.top: parent.top
    anchors.horizontalCenter: parent.horizontalCenter
    width: 1; height: 1
    system: rewardSystem
    emitRate: 0
    lifeSpan: 1000
    lifeSpanVariation: 500
    size: 10
    endSize: 2
    velocity: AngleDirection {
      angle: 90; angleVariation: 55
      magnitude: 500; magnitudeVariation: 100
    }
    acceleration: PointDirection { y: 200 }

    function reward() {
      burst(100)
    }
  }

  ItemParticle {
    parent: mapCanvasContainer
    system: rewardSystem
    delegate: Rectangle {
      width: 10
      height: 10
      radius: 5
      color: "red"
    }
  }

  function _isCompanionInstalled(uuid) {
    const apps = pluginManager.availableAppPlugins;
    if (!apps) {
      return false;
    }
    for (let i = 0; i < apps.length; ++i) {
      if (apps[i].uuid === uuid) {
        return true;
      }
    }
    return false;
  }

  function _instantiateCompanion(plugin, component) {
    const instance = component.createObject(fieldTM);
    if (instance) {
      _companionInstances.push(instance);
    } else {
      mainWindow.displayToast(qsTranslate("FieldTM", "Failed to load companion plugin: %1").arg(plugin.uuid));
    }
  }

  function loadCompanionPlugins() {
    for (let i = 0; i < _companionPlugins.length; ++i) {
      const plugin = _companionPlugins[i];
      // Upstream version already installed via the plugin manager - leave the user in control.
      if (_isCompanionInstalled(plugin.uuid)) {
        continue;
      }
      const component = Qt.createComponent(plugin.source);
      if (component.status === Component.Ready) {
        _instantiateCompanion(plugin, component);
      } else if (component.status === Component.Loading) {
        component.statusChanged.connect(function() {
          if (component.status === Component.Ready) {
            _instantiateCompanion(plugin, component);
          } else if (component.status === Component.Error) {
            mainWindow.displayToast(qsTranslate("FieldTM", "Failed to load companion plugin %1: %2").arg(plugin.uuid).arg(component.errorString()));
          }
        });
      } else {
        mainWindow.displayToast(qsTranslate("FieldTM", "Failed to load companion plugin %1: %2").arg(plugin.uuid).arg(component.errorString()));
      }
    }
  }

  // Quote a value as a QGIS expression string literal ('' escapes ').
  function quoteExpressionString(value) {
    return "'" + String(value === undefined || value === null ? "" : value).split("'").join("''") + "'";
  }

  function taskIntersectsExpression(task) {
    return `intersects(@geometry, geom_from_wkt(${quoteExpressionString(task.geometry.asWkt(8))}))`;
  }

  function taskAttribute(task, name) {
    const value = task.attribute(name);
    return value === undefined || value === null ? "" : String(value);
  }

  function isAssignedToMe(task) {
    return fieldTM.currentUser !== "" && taskAttribute(task, "assigned_to").toLowerCase() === fieldTM.currentUser.toLowerCase();
  }

  // Name of whoever else holds the task, or "" if it is free / ours.
  function otherAssignee(task) {
    if (isAssignedToMe(task)) {
      return "";
    }
    const assignee = taskAttribute(task, "assigned_to");
    if (assignee !== "") {
      return assignee;
    }
    return taskAttribute(task, "status") === "in_progress" ? qsTranslate("FieldTM", "another mapper") : "";
  }

  function taskInfoSummary(task) {
    let lines = [qsTranslate("FieldTM", "Task #%1").arg(taskAttribute(task, "task_id"))];
    const group = taskAttribute(task, "assigned_group");
    const assignee = taskAttribute(task, "assigned_to");
    const comment = taskAttribute(task, "comment");
    if (group !== "") {
      lines.push(qsTranslate("FieldTM", "Team: %1").arg(group));
    }
    if (assignee !== "") {
      lines.push(qsTranslate("FieldTM", "Assigned to: %1").arg(assignee));
    }
    if (comment !== "") {
      lines.push(comment);
    }
    return lines.length > 1 ? lines.join("\n") : "";
  }

  function setTaskAttributes(task, values) {
    fieldTM.tasksLayer.startEditing();
    for (const name in values) {
      fieldTM.tasksLayer.changeAttributeValue(task.id, fieldTM.tasksLayer.fields.indexOf(name), values[name]);
      task.setAttribute(name, values[name]);
    }
    fieldTM.tasksLayer.commitChanges();
    pushToCloud();
    refreshMyTasks();
  }

  function claimTask(task) {
    if (!fieldTM.reader && taskAttribute(task, "assigned_to") === "") {
      setTaskAttributes(task, { "assigned_to": fieldTM.currentUser });
      return true;
    }
    return false;
  }

  function releaseTask(task) {
    let values = { "assigned_to": "" };
    if (taskAttribute(task, "status") !== "completed") {
      values["status"] = "available";
    }
    setTaskAttributes(task, values);
  }

  function enterTask(task, claim) {
    fieldTM.currentTask = task;
    const taskId = taskAttribute(task, "task_id");
    if (fieldTM.reader) {
      mainWindow.displayToast(qsTranslate("FieldTM", "Viewing task #%1").arg(taskId));
    } else if (claim && claimTask(task)) {
      mainWindow.displayToast(qsTranslate("FieldTM", "Assigned task #%1").arg(taskId));
    } else {
      mainWindow.displayToast(qsTranslate("FieldTM", "Entered task #%1").arg(taskId));
    }
  }

  function refreshMyTasks() {
    let ids = [];
    if (fieldTM.currentUser !== "") {
      let it = LayerUtils.createFeatureIteratorFromExpression(fieldTM.tasksLayer, `lower(coalesce("assigned_to", '')) = lower(${quoteExpressionString(fieldTM.currentUser)}) and coalesce("status", '') != 'completed'`);
      while (it.hasNext()) {
        ids.push(it.next().attribute("task_id"));
      }
      delete it;
    }
    ids.sort((a, b) => a - b);
    fieldTM.myTaskIds = ids;
  }

  function zoomToMyTasks() {
    if (fieldTM.myTaskIds.length === 0) {
      return;
    }
    let it = LayerUtils.createFeatureIteratorFromExpression(fieldTM.tasksLayer, `"task_id" = ${quoteExpressionString(fieldTM.myTaskIds[0])}`);
    if (it.hasNext()) {
      const task = it.next();
      const rectangle = GeometryUtils.reprojectRectangle(GeometryUtils.boundingBox(task.geometry), fieldTM.tasksLayer.crs, mapCanvas.mapSettings.destinationCrs);
      mapCanvas.mapSettings.setExtent(rectangle, true);
    }
    delete it;
  }

  function pushToCloud() {
    if (fieldTM.cloudProjectsModel.currentProject && fieldTM.cloudProjectsModel.currentProject.status === QFieldCloudProject.Idle) {
      fieldTM.cloudProjectsModel.projectPush(fieldTM.cloudProjectsModel.currentProjectId, false);
    }
  }

  function synchronizeCloud() {
    if (fieldTM.cloudProjectsModel.currentProject && fieldTM.cloudProjectsModel.currentProject.status === QFieldCloudProject.Idle) {
      fieldTM.cloudProjectsModel.projectPush(fieldTM.cloudProjectsModel.currentProjectId, true);
    }
  }

  function checkOutdated() {
    if (fieldTM.cloudProjectsModel.currentProject && fieldTM.cloudProjectsModel.currentProject.status === QFieldCloudProject.Idle) {
      // If we last synchronized / downloaded the project over 30 min ago, we're outdated
      const lastLocalExportedAt = new Date(fieldTM.cloudProjectsModel.currentProject.lastLocalExportedAt);
      fieldTM.outdated = (Date.now() - lastLocalExportedAt.getTime()) / 1000 > 1800;
    } else {
      // Not being viewed in a cloud context
      fieldTM.outdated = false;
    }
  }

  function updateCurrentTaskStatus() {
    if (fieldTM.currentTask != undefined && !fieldTM.reader) {
      // If it hadn't been assigned yet, lay claim on it
      if (fieldTM.currentTask.attribute("status") === "available") {
        setTaskAttributes(fieldTM.currentTask, { "status": "in_progress" });
      }

      if (!fieldTM.currentTaskHasAddedFeature && fieldTM.currentTask.attribute("status") !== "completed") {
        // Check if the task is ready to be marked as complete
        let it = LayerUtils.createFeatureIteratorFromExpression(fieldTM.surveyLayer, taskIntersectsExpression(fieldTM.currentTask))
        let markAsCompleted = it.hasNext()
        while (it.hasNext()) {
          const feature = it.next()
          if (feature.attribute("status") == "") { // type coercion required
            markAsCompleted = false;
          }
        }
        delete it;

        if (markAsCompleted) {
          setTaskAttributes(fieldTM.currentTask, { "status": "completed" });

          mainWindow.displayToast(qsTranslate("FieldTM", "Completed task #%1").arg(fieldTM.currentTask.attribute("task_id")));
          rewardEmitter.reward();

          if (!fieldTM.singleTaskMode) {
            fieldTM.currentTask = undefined;
          }
        }
      }
    }
  }

  Connections {
    id: cloudProjectConnection
    target: fieldTM.cloudProjectsModel.currentProject ? fieldTM.cloudProjectsModel.currentProject : null

    property bool downloadTriggered: false

    function onStatusChanged() {
      if (fieldTM.cloudProjectsModel.currentProject.status === QFieldCloudProject.Downloading) {
        cloudProjectConnection.downloadTriggered = true;
      } else if (fieldTM.cloudProjectsModel.currentProject.status === QFieldCloudProject.Idle) {
        if (cloudProjectConnection.downloadTriggered) {
          cloudProjectConnection.downloadTriggered = false;
          fieldTM.busyOverlay.state = "hidden";
        }
      }
    }

    function onLastLocalExportedAtChanged() {
      checkOutdated();
    }
  }

  Connections {
    id: surveyLayerConnection
    target: surveyLayer
    enabled: fieldTM.currentTask !== undefined

    function onCommittedFeaturesAdded(layerId, addedFeatures) {
      fieldTM.currentTaskHasAddedFeature = true;
    }

    function onCommittedFeaturesRemoved(layerId, deletedFeatureIds) {
      updateCurrentTaskStatus();
    }

    function onCommittedAttributeValuesChanges(layerId, changedAttributesValues) {
      updateCurrentTaskStatus();
    }

    function onCommittedGeometriesChanges(layerId, changedGeometries) {
      updateCurrentTaskStatus();
    }
  }

  onCurrentTaskChanged: {
    fieldTM.currentTaskHasAddedFeature = false

    if (currentTask != undefined) {
      ExpressionContextUtils.setLayerVariable(tasksLayer, "current_task_id", currentTask.attribute("task_id"));
      // Hide tasks from identify while inside a task so taps land on buildings
      // without a disambiguation popup. Bit 0 = QgsMapLayer::Identifiable.
      tasksLayer.flags = tasksLayer.flags & ~1;
    } else {
      ExpressionContextUtils.setLayerVariable(tasksLayer, "current_task_id", -1);
      fieldTM.featureListForm.model.clear();
      tasksLayer.flags = tasksLayer.flags | 1;
    }

    tasksLayer.triggerRepaint();
  }

  Component.onCompleted: {
    // Adjust app-wide settings to increase user-friendlyness
    fieldTM.qfieldSettings.autoOpenFormSingleIdentify = true;
    fieldTM.qfieldSettings.autoZoomToIdentifiedFeature = true;

    fieldTM.currentUser = projectInfo.cloudUserInformation.username || "";
    fieldTM.reader = cloudProjectsModel.currentProject && cloudProjectsModel.currentProject.userRole === "reader";
    ExpressionContextUtils.setLayerVariable(tasksLayer, "fieldtm_current_user", fieldTM.currentUser);

    // Single-task projects skip the locking UX: auto-claim the lone task so taps
    // land directly on the survey layer.
    let allTasksIt = LayerUtils.createFeatureIteratorFromExpression(fieldTM.tasksLayer, "1=1");
    let firstTask = allTasksIt.hasNext() ? allTasksIt.next() : null;
    let hasSecondTask = allTasksIt.hasNext();
    delete allTasksIt;
    fieldTM.singleTaskMode = firstTask !== null && !hasSecondTask;

    if (fieldTM.singleTaskMode) {
      fieldTM.currentTask = firstTask;
      claimTask(firstTask);
    } else {
      let it = LayerUtils.createFeatureIteratorFromExpression(fieldTM.tasksLayer, `"status" = 'in_progress' and lower(coalesce("assigned_to", '')) = lower(${quoteExpressionString(fieldTM.currentUser)})`);
      fieldTM.currentTask = it.hasNext() ? it.next() : undefined;
      delete it;
    }
    refreshMyTasks();
    if (fieldTM.currentTask === undefined) {
      zoomToMyTasks();
    }

    const pointHandler = iface.findItemByObjectName("pointHandler");
    pointHandler.registerHandler("fieldTM", (point, type, interactionType) => {
                                   if (fieldTM.currentTask != undefined) {
                                     if (interactionType === "clicked") {
                                       const tl = fieldTM.mapCanvas.mapSettings.screenToCoordinate(Qt.point(point.x - 4, point.y - 4));
                                       const br = fieldTM.mapCanvas.mapSettings.screenToCoordinate(Qt.point(point.x + 4, point.y + 4));
                                       const rectangle = GeometryUtils.reprojectRectangle(GeometryUtils.createRectangleFromPoints(tl, br), fieldTM.mapCanvas.mapSettings.destinationCrs, fieldTM.surveyLayer.crs);
                                       let it = LayerUtils.createFeatureIteratorFromRectangle(fieldTM.surveyLayer, rectangle);
                                       while (it.hasNext()) {
                                         const feature = it.next();
                                         if (GeometryUtils.geometryWithin(feature.geometry, fieldTM.currentTask.geometry) || GeometryUtils.geometryOverlaps(feature.geometry, fieldTM.currentTask.geometry)) {
                                           delete it;
                                           return false;
                                         }
                                       }
                                       delete it;
                                       return true;
                                     }
                                     return false;
                                   }

                                   const tl = mapCanvas.mapSettings.screenToCoordinate(Qt.point(point.x - 4, point.y - 4));
                                   const br = mapCanvas.mapSettings.screenToCoordinate(Qt.point(point.x + 4, point.y + 4));
                                   const rectangle = GeometryUtils.reprojectRectangle(GeometryUtils.createRectangleFromPoints(tl, br), mapCanvas.mapSettings.destinationCrs, fieldTM.tasksLayer.crs);

                                   let it = LayerUtils.createFeatureIteratorFromRectangle(fieldTM.tasksLayer, rectangle);
                                   const task = it.hasNext() ? it.next() : undefined;
                                   delete it;
                                   if (task !== undefined) {
                                     const other = fieldTM.reader ? "" : otherAssignee(task);
                                     if (other !== "") {
                                       fieldTM.pendingTask = task;
                                       takeoverDialog.assignee = other;
                                       takeoverDialog.open();
                                     } else {
                                       enterTask(task, true);
                                     }
                                   }
                                   return true;
                                 });

    checkOutdated();
    loadCompanionPlugins();
  }

  Component.onDestruction: {
    const pointHandler = iface.findItemByObjectName("pointHandler");
    pointHandler.deregisterHandler("fieldTM");
  }
}
