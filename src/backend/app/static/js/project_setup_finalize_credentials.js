import { renderCallout } from "./project_setup_shared.js";

export function initProjectSetupFinalizeCredentials({
  i18nStrings,
  projectType,
  advancedOptionsToggle,
  credentialsModal,
  credentialsForm,
  credentialsError,
  odkCredentialsFields,
  qfieldCredentialsFields,
  cancelCredsBtn,
  testCredsBtn,
  saveCredsBtn,
  showFinaliseConfirmDialog,
}) {
  const isOdk = projectType === "ODK";
  const isQField = projectType === "QField";
  const OFFICIAL_QFIELDCLOUD_URL = "https://app.qfield.cloud";
  let customCreds = null;

  function getQFieldMode() {
    const modeRadio = document.getElementById("qfield-mode-radio");
    return modeRadio?.value === "custom" ? "custom" : "official";
  }

  function showError(message, variant = "danger") {
    if (credentialsError) {
      renderCallout(credentialsError, variant, message);
    }
  }

  function getCredentials() {
    if (isOdk) {
      return {
        url: document.getElementById("odk-url-input")?.value?.trim(),
        username: document.getElementById("odk-username-input")?.value?.trim(),
        password: document.getElementById("odk-password-input")?.value?.trim(),
      };
    }
    if (isQField) {
      const mode = getQFieldMode();
      const url =
        mode === "custom"
          ? document.getElementById("qfield-url-input")?.value?.trim()
          : OFFICIAL_QFIELDCLOUD_URL;
      return {
        url,
        username: document.getElementById("qfield-username-input")?.value?.trim(),
        password: document.getElementById("qfield-password-input")?.value?.trim(),
        org: document.getElementById("qfield-org-input")?.value?.trim() || "",
        mode,
      };
    }
    return null;
  }

  function resetModal() {
    if (credentialsModal) credentialsModal.open = false;
    if (credentialsForm) credentialsForm.reset();
    if (credentialsError) credentialsError.innerHTML = "";
    customCreds = null;
  }

  if (advancedOptionsToggle && credentialsModal) {
    advancedOptionsToggle.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();

      if (!isOdk && !isQField) {
        showError(i18nStrings.projectTypeNotSet, "warning");
        credentialsModal.open = true;
        return;
      }

      if (isOdk) {
        credentialsModal.label = i18nStrings.customOdkCredentials;
        odkCredentialsFields.hidden = false;
        qfieldCredentialsFields.hidden = true;
      } else if (isQField) {
        credentialsModal.label = i18nStrings.customQFieldCredentials;
        odkCredentialsFields.hidden = true;
        qfieldCredentialsFields.hidden = false;
        updateQFieldUrlVisibility();
      }

      credentialsModal.open = true;
    });
  }

  function updateQFieldUrlVisibility() {
    const urlInput = document.getElementById("qfield-url-input");
    if (urlInput) urlInput.hidden = getQFieldMode() !== "custom";
  }

  if (isQField) {
    const modeRadio = document.getElementById("qfield-mode-radio");
    if (modeRadio) {
      modeRadio.addEventListener("change", function () {
        updateQFieldUrlVisibility();
        // Switching modes invalidates any previously-tested credentials
        customCreds = null;
        if (credentialsError) credentialsError.innerHTML = "";
      });
    }
  }

  if (cancelCredsBtn) {
    cancelCredsBtn.addEventListener("click", resetModal);
  }

  if (testCredsBtn) {
    testCredsBtn.addEventListener("click", async function () {
      const creds = getCredentials();

      if (!creds || !creds.url || !creds.username || !creds.password) {
        showError(i18nStrings.pleaseFillAllFields, "danger");
        return;
      }

      try {
        testCredsBtn.loading = true;
        showError(i18nStrings.testingCredentials, "info");

        let response;

        if (isOdk) {
          response = await fetch("/api/v1/central/test-credentials", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              external_project_instance_url: creds.url,
              external_project_username: creds.username,
              external_project_password: creds.password,
            }),
          });
        } else if (isQField) {
          response = await fetch("/api/v1/qfield/test-credentials", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              qfield_cloud_url: creds.url,
              qfield_cloud_user: creds.username,
              qfield_cloud_password: creds.password,
              qfield_cloud_org: creds.org || null,
            }),
          });
        }

        if (response.ok) {
          showError(i18nStrings.credentialsValid, "success");
          customCreds = creds;
        } else {
          const error = await response.json();
          showError(error.detail || i18nStrings.invalidCredentials, "danger");
          customCreds = null;
        }
      } catch (error) {
        showError(
          i18nStrings.errorTestingCredentialsFormat.replace("%(message)s", error.message),
          "danger",
        );
        customCreds = null;
      } finally {
        testCredsBtn.loading = false;
      }
    });
  }

  function saveCredentials(e) {
    e.preventDefault();
    if (!customCreds) {
      showError(i18nStrings.pleaseTestCredentialsFirst, "warning");
      return;
    }
    credentialsModal.open = false;
    showFinaliseConfirmDialog();
  }

  if (saveCredsBtn) saveCredsBtn.addEventListener("click", saveCredentials);
  if (credentialsForm) credentialsForm.addEventListener("submit", saveCredentials);

  return {
    getCustomCreds() {
      return customCreds;
    },
  };
}
