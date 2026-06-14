// Task assignment panel: Leaflet selection map over the stored task areas.
//
// Progressive enhancement on top of assignment_panel.html - the summary
// table and save form work without this module. Edits are staged in a
// draft diff mirrored to sessionStorage (server stays authoritative) and
// submitted through the hidden "assignments" form field as JSON of
// {task_id: {assigned_to, assigned_group}}. Assignments are advisory
// metadata; task status is owned by the field apps and never written here.
//
// All user-visible text comes from the i18nStrings object passed in, and
// user-supplied values (assignee names, group labels) only ever reach the
// DOM via textContent/createTextNode - never innerHTML.

import { clearContainer, renderCallout } from "./project_setup_shared.js";

const UNASSIGNED_COLOR = "#ff7800";
const GROUP_LABEL_PATTERN = /^[a-zA-Z0-9_-]*$/;

let activeMap = null;
let activeCleanup = null;

function formatString(template, params) {
  let formatted = String(template);
  for (const [key, value] of Object.entries(params)) {
    formatted = formatted.replace("%(" + key + ")s", String(value));
  }
  return formatted;
}

function colorForLabel(label) {
  // Deterministic colour per group/assignee label so the map styling is
  // stable across reloads without storing a palette anywhere.
  let hash = 0;
  for (let i = 0; i < label.length; i++) {
    hash = (hash * 31 + label.charCodeAt(i)) | 0;
  }
  const hue = ((hash % 360) + 360) % 360;
  return "hsl(" + hue + ", 70%, 40%)";
}

function destroyExistingMap(container) {
  if (activeMap) {
    try {
      activeMap.remove();
    } catch (e) {
      // Already removed alongside its container.
    }
    activeMap = null;
  }
  if (container._leaflet_id) {
    // Same stale-instance guard as render_leaflet_map in map_helpers.py:
    // a previous panel render may have left a Leaflet stamp on a reused
    // container, which would make L.map() throw "already initialized".
    try {
      const staleMap = L.Map.prototype.get(container._leaflet_id);
      if (staleMap) staleMap.remove();
    } catch (e) {
      // No retrievable instance; fall through and clear the stamp.
    }
    delete container._leaflet_id;
  }
}

export function initAssignmentPanel({ projectId, i18nStrings }) {
  // The panel fragment can be swapped in repeatedly (htmx re-loads on
  // navigation), so tear down any previous instance first.
  if (activeCleanup) {
    activeCleanup();
    activeCleanup = null;
  }

  const savedEventName = i18nStrings.savedEvent || "assignment:saved";
  const draftStorageKey = "ftm-draft-assignments-" + projectId;

  function setUpPanel(mapContainer) {
    const assigneeInput = document.getElementById("assignment-assignee-input");
    const groupInput = document.getElementById("assignment-group-input");
    const applyBtn = document.getElementById("assignment-apply-btn");
    const unassignBtn = document.getElementById("assignment-unassign-btn");
    const autoGroupBtn = document.getElementById("assignment-autogroup-btn");
    const clearBtn = document.getElementById("assignment-clear-btn");
    const payloadInput = document.getElementById("assignment-payload");
    const messagesRegion = document.getElementById("assignment-messages");
    const bannerRegion = document.getElementById("assignment-draft-banner");

    const selectedTaskIds = new Set();
    // taskId (string) -> {assigned_to?, assigned_group?}; only keys that
    // differ from the server value are kept, so the draft is a pure diff.
    let draftEdits = readDraftStorage();
    // taskId (string) -> {assigned_to, assigned_group} as last fetched.
    let serverProperties = {};
    const layersByTaskId = {};
    let taskLayer = null;

    destroyExistingMap(mapContainer);
    const map = L.map(mapContainer).setView([0, 0], 2);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OSM contributors",
      maxZoom: 19,
    }).addTo(map);
    activeMap = map;
    setTimeout(function () {
      map.invalidateSize();
    }, 100);

    function readDraftStorage() {
      try {
        const raw = window.sessionStorage.getItem(draftStorageKey);
        const parsed = raw ? JSON.parse(raw) : null;
        return parsed && typeof parsed === "object" ? parsed : {};
      } catch (e) {
        return {};
      }
    }

    function writeDraftStorage() {
      try {
        if (Object.keys(draftEdits).length > 0) {
          window.sessionStorage.setItem(draftStorageKey, JSON.stringify(draftEdits));
        } else {
          window.sessionStorage.removeItem(draftStorageKey);
        }
      } catch (e) {
        // Ignore storage failures; the draft still lives in memory.
      }
    }

    function effectiveProperties(taskId) {
      const server = serverProperties[String(taskId)] || { assigned_to: "", assigned_group: "" };
      return { ...server, ...(draftEdits[String(taskId)] || {}) };
    }

    function styleForTask(taskId) {
      const props = effectiveProperties(taskId);
      let color = UNASSIGNED_COLOR;
      if (props.assigned_group) {
        color = colorForLabel(props.assigned_group);
      } else if (props.assigned_to) {
        color = colorForLabel(props.assigned_to);
      }
      const selected = selectedTaskIds.has(Number(taskId));
      return {
        color: color,
        weight: selected ? 6 : 3,
        opacity: selected ? 1 : 0.8,
        fillOpacity: selected ? 0.45 : 0.3,
      };
    }

    function buildTaskLabel(taskId) {
      const props = effectiveProperties(taskId);
      const wrapper = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = formatString(i18nStrings.taskLabelFormat, { task_id: taskId });
      wrapper.appendChild(title);
      if (props.assigned_group) {
        wrapper.appendChild(document.createElement("br"));
        wrapper.appendChild(
          document.createTextNode(
            formatString(i18nStrings.groupLabelFormat, { group: props.assigned_group }),
          ),
        );
      }
      wrapper.appendChild(document.createElement("br"));
      wrapper.appendChild(
        document.createTextNode(
          props.assigned_to
            ? formatString(i18nStrings.assignedToFormat, { name: props.assigned_to })
            : i18nStrings.unassigned,
        ),
      );
      return wrapper;
    }

    function setDraftValue(taskId, key, value) {
      const taskKey = String(taskId);
      const server = serverProperties[taskKey] || { assigned_to: "", assigned_group: "" };
      const entry = draftEdits[taskKey] || {};
      if (value === server[key]) {
        delete entry[key];
      } else {
        entry[key] = value;
      }
      if (Object.keys(entry).length > 0) {
        draftEdits[taskKey] = entry;
      } else {
        delete draftEdits[taskKey];
      }
    }

    function sanitizeDraft(rawDraft) {
      // The draft is a diff replayed over fresh server data: entries for
      // vanished task ids, malformed values, or values now matching the
      // server are dropped.
      const sanitized = {};
      for (const [taskKey, entry] of Object.entries(rawDraft)) {
        const server = serverProperties[taskKey];
        if (!server || !entry || typeof entry !== "object") continue;
        const cleaned = {};
        if (typeof entry.assigned_to === "string" && entry.assigned_to !== server.assigned_to) {
          cleaned.assigned_to = entry.assigned_to;
        }
        if (
          typeof entry.assigned_group === "string" &&
          GROUP_LABEL_PATTERN.test(entry.assigned_group) &&
          entry.assigned_group !== server.assigned_group
        ) {
          cleaned.assigned_group = entry.assigned_group;
        }
        if (Object.keys(cleaned).length > 0) sanitized[taskKey] = cleaned;
      }
      return sanitized;
    }

    function discardDraft() {
      draftEdits = {};
      afterDraftChange();
    }

    function updateDraftBanner() {
      if (!bannerRegion) return;
      clearContainer(bannerRegion);
      const count = Object.keys(draftEdits).length;
      if (count === 0) return;
      const callout = document.createElement("wa-callout");
      callout.setAttribute("variant", "warning");
      const span = document.createElement("span");
      span.textContent = formatString(i18nStrings.unsavedChangesFormat, { count: count });
      callout.appendChild(span);
      const discardBtn = document.createElement("button");
      discardBtn.type = "button";
      discardBtn.className = "wa-button wa-button--default";
      discardBtn.style.marginInlineStart = "8px";
      discardBtn.textContent = i18nStrings.discardChanges;
      discardBtn.addEventListener("click", discardDraft);
      callout.appendChild(discardBtn);
      bannerRegion.appendChild(callout);
    }

    function afterDraftChange() {
      writeDraftStorage();
      if (payloadInput) payloadInput.value = JSON.stringify(draftEdits);
      updateDraftBanner();
      restyleTaskLayers();
    }

    function restyleTaskLayers() {
      for (const [taskKey, layer] of Object.entries(layersByTaskId)) {
        layer.setStyle(styleForTask(Number(taskKey)));
      }
    }

    function updateApplyButton() {
      if (!applyBtn) return;
      applyBtn.textContent =
        selectedTaskIds.size > 0
          ? formatString(i18nStrings.applyToSelectedFormat, { count: selectedTaskIds.size })
          : i18nStrings.applyToSelected;
    }

    function syncTableCheckboxes() {
      const checkboxes = document.querySelectorAll(".assignment-task-checkbox");
      let allChecked = checkboxes.length > 0;
      let anyChecked = false;
      checkboxes.forEach(function (checkbox) {
        const checked = selectedTaskIds.has(Number(checkbox.dataset.taskId));
        checkbox.checked = checked;
        allChecked = allChecked && checked;
        anyChecked = anyChecked || checked;
      });
      const selectAll = document.getElementById("assignment-select-all");
      if (selectAll) {
        selectAll.checked = allChecked;
        selectAll.indeterminate = anyChecked && !allChecked;
      }
    }

    function refreshSelectionUI() {
      restyleTaskLayers();
      updateApplyButton();
      syncTableCheckboxes();
    }

    function toggleSelection(taskId, extend) {
      // Plain click replaces the selection with the clicked task (clicking
      // the sole selected task deselects it); shift-click extends by
      // toggling membership without clearing the rest.
      if (extend) {
        if (selectedTaskIds.has(taskId)) {
          selectedTaskIds.delete(taskId);
        } else {
          selectedTaskIds.add(taskId);
        }
      } else {
        const wasOnlySelection = selectedTaskIds.size === 1 && selectedTaskIds.has(taskId);
        selectedTaskIds.clear();
        if (!wasOnlySelection) selectedTaskIds.add(taskId);
      }
      refreshSelectionUI();
    }

    function enhanceSummaryTable() {
      // Add a selection checkbox column to the server-rendered summary
      // table; map and table share the same selection set. The table is
      // re-rendered by the save POST, so this runs again after each swap.
      const table = document.getElementById("assignment-summary-table");
      if (!table || table.dataset.selectionEnhanced) return;
      table.dataset.selectionEnhanced = "true";

      const headerRow = table.querySelector("thead tr");
      if (headerRow) {
        const th = document.createElement("th");
        th.style.padding = "6px 8px";
        const selectAll = document.createElement("input");
        selectAll.type = "checkbox";
        selectAll.id = "assignment-select-all";
        selectAll.setAttribute("aria-label", i18nStrings.selectAllTasks);
        selectAll.addEventListener("change", function () {
          table.querySelectorAll(".assignment-task-checkbox").forEach(function (checkbox) {
            const taskId = Number(checkbox.dataset.taskId);
            if (selectAll.checked) {
              selectedTaskIds.add(taskId);
            } else {
              selectedTaskIds.delete(taskId);
            }
          });
          refreshSelectionUI();
        });
        th.appendChild(selectAll);
        headerRow.insertBefore(th, headerRow.firstElementChild);
      }

      table.querySelectorAll("tbody tr[data-task-id]").forEach(function (row) {
        const taskId = Number(row.dataset.taskId);
        if (!Number.isFinite(taskId)) return;
        const td = document.createElement("td");
        td.style.padding = "6px 8px";
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "assignment-task-checkbox";
        checkbox.dataset.taskId = String(taskId);
        checkbox.setAttribute(
          "aria-label",
          formatString(i18nStrings.selectTaskFormat, { task_id: taskId }),
        );
        checkbox.addEventListener("change", function () {
          if (checkbox.checked) {
            selectedTaskIds.add(taskId);
          } else {
            selectedTaskIds.delete(taskId);
          }
          refreshSelectionUI();
        });
        td.appendChild(checkbox);
        row.insertBefore(td, row.firstElementChild);
      });

      syncTableCheckboxes();
    }

    function renderTaskLayer(featureCollection) {
      if (taskLayer) {
        map.removeLayer(taskLayer);
        taskLayer = null;
      }
      for (const taskKey of Object.keys(layersByTaskId)) {
        delete layersByTaskId[taskKey];
      }

      serverProperties = {};
      (featureCollection.features || []).forEach(function (feature) {
        const props = feature.properties || {};
        if (props.task_id === undefined || props.task_id === null) return;
        serverProperties[String(props.task_id)] = {
          assigned_to: typeof props.assigned_to === "string" ? props.assigned_to : "",
          assigned_group: typeof props.assigned_group === "string" ? props.assigned_group : "",
        };
      });
      draftEdits = sanitizeDraft(draftEdits);
      Array.from(selectedTaskIds).forEach(function (taskId) {
        if (!serverProperties[String(taskId)]) selectedTaskIds.delete(taskId);
      });

      taskLayer = L.geoJSON(featureCollection, {
        style: function (feature) {
          return styleForTask((feature.properties || {}).task_id);
        },
        onEachFeature: function (feature, layer) {
          const taskId = (feature.properties || {}).task_id;
          if (taskId === undefined || taskId === null) return;
          layersByTaskId[String(taskId)] = layer;
          layer.on("click", function (event) {
            toggleSelection(Number(taskId), Boolean(event.originalEvent && event.originalEvent.shiftKey));
          });
          // Content function so the label reflects draft edits when shown.
          layer.bindTooltip(
            function () {
              return buildTaskLabel(taskId);
            },
            { sticky: true },
          );
        },
      }).addTo(map);

      if (taskLayer.getBounds().isValid()) {
        map.fitBounds(taskLayer.getBounds());
      }
      afterDraftChange();
      refreshSelectionUI();
    }

    function loadTaskAreas() {
      return fetch("/projects/" + projectId + "/assignments/geojson")
        .then(function (response) {
          if (!response.ok) throw new Error("HTTP " + response.status);
          return response.json();
        })
        .then(function (featureCollection) {
          renderTaskLayer(featureCollection);
        })
        .catch(function () {
          renderCallout(messagesRegion, "danger", i18nStrings.loadFailed);
        });
    }

    function applyToSelected() {
      clearContainer(messagesRegion);
      if (selectedTaskIds.size === 0) {
        renderCallout(messagesRegion, "warning", i18nStrings.noSelection);
        return;
      }
      const group = groupInput ? groupInput.value.trim() : "";
      if (!GROUP_LABEL_PATTERN.test(group)) {
        renderCallout(messagesRegion, "danger", i18nStrings.invalidGroupLabel);
        return;
      }
      const assignee = assigneeInput ? assigneeInput.value.trim() : "";
      if (!assignee && !group) {
        renderCallout(messagesRegion, "warning", i18nStrings.nothingToApply);
        return;
      }
      // Only stage the fields the user actually filled in, so applying a
      // group label alone never silently clears existing assignees;
      // intentional clearing goes through "Unassign selected" instead.
      selectedTaskIds.forEach(function (taskId) {
        if (assignee) setDraftValue(taskId, "assigned_to", assignee);
        if (group) setDraftValue(taskId, "assigned_group", group);
      });
      afterDraftChange();
    }

    function unassignSelected() {
      // Explicit clear affordance: stages empty assignee and group for the
      // selection ("" means unassigned/ungrouped on the server).
      clearContainer(messagesRegion);
      if (selectedTaskIds.size === 0) {
        renderCallout(messagesRegion, "warning", i18nStrings.noSelection);
        return;
      }
      selectedTaskIds.forEach(function (taskId) {
        setDraftValue(taskId, "assigned_to", "");
        setDraftValue(taskId, "assigned_group", "");
      });
      afterDraftChange();
    }

    function autoGroupByQuadrant() {
      // Bucket every task into NE/NW/SE/SW by where its bounds centre
      // falls relative to the bbox centre of the whole task layer.
      if (!taskLayer || !taskLayer.getBounds().isValid()) return;
      clearContainer(messagesRegion);
      const center = taskLayer.getBounds().getCenter();
      for (const [taskKey, layer] of Object.entries(layersByTaskId)) {
        const taskCenter = layer.getBounds ? layer.getBounds().getCenter() : layer.getLatLng();
        if (!taskCenter) continue;
        const quadrant =
          (taskCenter.lat >= center.lat ? "N" : "S") + (taskCenter.lng >= center.lng ? "E" : "W");
        setDraftValue(taskKey, "assigned_group", quadrant);
      }
      afterDraftChange();
    }

    if (applyBtn) applyBtn.addEventListener("click", applyToSelected);
    if (unassignBtn) unassignBtn.addEventListener("click", unassignSelected);
    if (autoGroupBtn) autoGroupBtn.addEventListener("click", autoGroupByQuadrant);
    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        selectedTaskIds.clear();
        refreshSelectionUI();
      });
    }

    function onSaved(event) {
      const detail = event.detail || {};
      if (detail.projectId !== undefined && Number(detail.projectId) !== Number(projectId)) {
        return;
      }
      // Server is authoritative again: drop the draft and re-fetch.
      draftEdits = {};
      afterDraftChange();
      loadTaskAreas();
    }

    function onSummarySwap(event) {
      if (event.target && event.target.id === "assignment-summary-region") {
        enhanceSummaryTable();
      }
    }

    document.body.addEventListener(savedEventName, onSaved);
    document.body.addEventListener("htmx:afterSwap", onSummarySwap);

    activeCleanup = function () {
      document.body.removeEventListener(savedEventName, onSaved);
      document.body.removeEventListener("htmx:afterSwap", onSummarySwap);
      try {
        map.remove();
      } catch (e) {
        // Already removed alongside its container.
      }
      if (activeMap === map) activeMap = null;
    };

    enhanceSummaryTable();
    updateApplyButton();
    if (payloadInput) payloadInput.value = JSON.stringify(draftEdits);
    loadTaskAreas();
  }

  // Deferred init per render_leaflet_map in map_helpers.py: wait for the
  // container to be swapped into the DOM and for the Leaflet global.
  function start() {
    const mapContainer = document.getElementById("assignment-map");
    if (!mapContainer) return;
    if (typeof L === "undefined") {
      setTimeout(start, 100);
      return;
    }
    setUpPanel(mapContainer);
  }

  if (document.getElementById("assignment-map")) {
    start();
  } else {
    const onPanelSwap = function () {
      if (document.getElementById("assignment-map")) {
        document.body.removeEventListener("htmx:afterSwap", onPanelSwap);
        start();
      }
    };
    document.body.addEventListener("htmx:afterSwap", onPanelSwap);
    activeCleanup = function () {
      document.body.removeEventListener("htmx:afterSwap", onPanelSwap);
    };
  }
}
