import { renderCallout } from "./project_setup_shared.js";

export function initProjectSetupFinalizeCredentials({
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
}) {
  const isOdk = projectType === "ODK";
  const isQField = projectType === "QField";
  let customCreds = null;

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
      return {
        url: document.getElementById("qfield-url-input")?.value?.trim(),
        username: document.getElementById("qfield-username-input")?.value?.trim(),
        password: document.getElementById("qfield-password-input")?.value?.trim(),
      };
    }
    return null;
  }

  function resetModal() {
    if (credentialsModal) credentialsModal.classList.remove("ftm-modal-backdrop--visible");
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
        credentialsModal.classList.add("ftm-modal-backdrop--visible");
        return;
      }

      if (isOdk) {
        credentialsModalTitle.textContent = i18nStrings.customOdkCredentials;
        if (odkCredentialsFields) odkCredentialsFields.style.display = "block";
        if (qfieldCredentialsFields) qfieldCredentialsFields.style.display = "none";
      } else if (isQField) {
        credentialsModalTitle.textContent = i18nStrings.customQFieldCredentials;
        if (odkCredentialsFields) odkCredentialsFields.style.display = "none";
        if (qfieldCredentialsFields) qfieldCredentialsFields.style.display = "block";
      }

      credentialsModal.classList.add("ftm-modal-backdrop--visible");
    });
  }

  if (credentialsModal) {
    credentialsModal.addEventListener("click", function (e) {
      if (e.target === credentialsModal) {
        resetModal();
      }
    });
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
        testCredsBtn.disabled = true;
        testCredsBtn.textContent = i18nStrings.testing;
        showError(i18nStrings.testingCredentials, "info");

        let response;

        if (isOdk) {
          const params = new URLSearchParams({
            external_project_instance_url: creds.url,
            external_project_username: creds.username,
            external_project_password: creds.password,
          });
          response = await fetch(`/api/v1/central/test-credentials?${params}`, {
            method: "POST",
          });
        } else if (isQField) {
          response = await fetch("/api/v1/qfield/test-credentials", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              qfield_cloud_url: creds.url,
              qfield_cloud_user: creds.username,
              qfield_cloud_password: creds.password,
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
        testCredsBtn.disabled = false;
        testCredsBtn.textContent = i18nStrings.testCredentials;
      }
    });
  }

  if (saveCredsBtn && credentialsForm) {
    credentialsForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      if (!customCreds) {
        showError(i18nStrings.pleaseTestCredentialsFirst, "warning");
        return;
      }

      credentialsModal.classList.remove("ftm-modal-backdrop--visible");
      showFinaliseConfirmDialog();
    });
  }

  return {
    getCustomCreds() {
      return customCreds;
    },
  };
}
