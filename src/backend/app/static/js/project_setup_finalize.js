import { initProjectSetupFinalizeCredentials } from "./project_setup_finalize_credentials.js";
import { initProjectSetupFinalizeSubmit } from "./project_setup_finalize_submit.js";
import { renderCallout } from "./project_setup_shared.js";

export function initProjectSetupFinalize({ i18nStrings, projectId, projectType }) {
  const finaliseProjectBtn = document.getElementById("finalise-project-btn");
  const advancedOptionsToggle = document.getElementById("advanced-options-toggle");
  const finaliseActions = document.getElementById("finalise-actions");
  const finaliseStatus = document.getElementById("finalise-status");
  const finaliseConfirmDialog = document.getElementById("finalise-confirm-dialog");
  const finaliseConfirmMessage = document.getElementById("finalise-confirm-message");
  const finaliseConfirmBtn = document.getElementById("finalise-confirm-btn");
  const finaliseCancelBtn = document.getElementById("finalise-cancel-btn");
  const credentialsModal = document.getElementById("credentials-modal");
  const cancelCredsBtn = document.getElementById("cancel-creds-btn");
  const testCredsBtn = document.getElementById("test-creds-btn");
  const saveCredsBtn = document.getElementById("save-creds-btn");
  const credentialsForm = document.getElementById("credentials-form");
  const credentialsError = document.getElementById("credentials-error");
  const credentialsModalTitle = document.getElementById("credentials-modal-title");
  const odkCredentialsFields = document.getElementById("odk-credentials-fields");
  const qfieldCredentialsFields = document.getElementById("qfield-credentials-fields");
  const finaliseForm = document.getElementById("finalise-project-form");

  const isOdk = projectType === "ODK";
  const isQField = projectType === "QField";

  function showFinaliseActionsAsCompleted() {
    if (finaliseActions) {
      finaliseActions.style.display = "none";
      return;
    }
    if (finaliseProjectBtn) finaliseProjectBtn.style.display = "none";
    if (advancedOptionsToggle) advancedOptionsToggle.style.display = "none";
  }

  document.body.addEventListener(i18nStrings.finalizeCompleteEvent, function () {
    showFinaliseActionsAsCompleted();
  });

  document.body.addEventListener("click", function (event) {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const trigger = target.closest("#view-fieldtm-project-btn");
    if (!trigger) return;
    if (projectId) {
      window.location.assign(`/projects/${projectId}`);
    } else {
      window.location.reload();
    }
  });

  document.body.addEventListener(i18nStrings.step3CompleteEvent, function () {
    if (projectId) {
      window.location.assign(`/projects/${projectId}`);
    } else {
      window.location.reload();
    }
  });

  document.body.addEventListener(i18nStrings.step4PreviewReadyEvent, function () {
    setTimeout(function () {
      const mapContainer = document.getElementById("leaflet-map-split-preview");
      if (mapContainer) {
        mapContainer.scrollIntoView({ behavior: "smooth", block: "center" });
        return;
      }
      const splitStatus = document.getElementById("split-status");
      if (splitStatus) {
        splitStatus.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }, 300);
  });

  document.body.addEventListener(i18nStrings.step4CompleteEvent, function () {
    if (projectId) {
      window.location.assign(`/projects/${projectId}`);
    } else {
      window.location.reload();
    }
  });

  function getProjectTypeName() {
    if (isOdk) return i18nStrings.odkCentral;
    if (isQField) return i18nStrings.qfield;
    return i18nStrings.mappingTool;
  }

  function hideFinaliseConfirmDialog() {
    if (!finaliseConfirmDialog) return;

    if (typeof finaliseConfirmDialog.hide === "function") {
      finaliseConfirmDialog.hide();
    } else {
      finaliseConfirmDialog.removeAttribute("open");
    }
  }

  let getCustomCreds = () => null;
  const submitFinaliseProject = initProjectSetupFinalizeSubmit({
    i18nStrings,
    projectType,
    finaliseStatus,
    finaliseForm,
    finaliseProjectBtn,
    advancedOptionsToggle,
    finaliseConfirmBtn,
    finaliseCancelBtn,
    getCustomCreds: () => getCustomCreds(),
  });

  function showFinaliseConfirmDialog() {
    if (!isOdk && !isQField) {
      if (finaliseStatus) {
        renderCallout(finaliseStatus, "danger", i18nStrings.projectTypeNotSet);
      }
      return;
    }

    const projectTypeName = getProjectTypeName();
    if (finaliseConfirmMessage) {
      finaliseConfirmMessage.textContent = i18nStrings.finaliseConfirmFormat.replace(
        "%(project_type)s",
        projectTypeName,
      );
    }

    if (!finaliseConfirmDialog) {
      submitFinaliseProject();
      return;
    }

    if (typeof finaliseConfirmDialog.show === "function") {
      finaliseConfirmDialog.show();
    } else {
      finaliseConfirmDialog.setAttribute("open", "");
    }
  }

  const credentials = initProjectSetupFinalizeCredentials({
    i18nStrings,
    projectType,
    advancedOptionsToggle,
    credentialsModal,
    credentialsForm,
    credentialsError,
    credentialsModalTitle,
    odkCredentialsFields,
    qfieldCredentialsFields,
    cancelCredsBtn,
    testCredsBtn,
    saveCredsBtn,
    showFinaliseConfirmDialog,
  });
  getCustomCreds = credentials.getCustomCreds;

  if (finaliseCancelBtn) {
    finaliseCancelBtn.addEventListener("click", function () {
      hideFinaliseConfirmDialog();
    });
  }

  if (finaliseConfirmBtn) {
    finaliseConfirmBtn.addEventListener("click", function () {
      hideFinaliseConfirmDialog();
      submitFinaliseProject();
    });
  }

  if (finaliseProjectBtn) {
    finaliseProjectBtn.addEventListener("click", function () {
      showFinaliseConfirmDialog();
    });
  }
}
