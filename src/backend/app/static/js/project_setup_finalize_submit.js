import { renderCallout } from "./project_setup_shared.js";

export function initProjectSetupFinalizeSubmit({
  i18nStrings,
  projectType,
  finaliseStatus,
  finaliseForm,
  finaliseProjectBtn,
  advancedOptionsToggle,
  finaliseConfirmBtn,
  finaliseCancelBtn,
  getCustomCreds,
}) {
  const isOdk = projectType === "ODK";
  const isQField = projectType === "QField";

  function getProjectTypeName() {
    if (isOdk) return i18nStrings.odkCentral;
    if (isQField) return i18nStrings.qfield;
    return i18nStrings.mappingTool;
  }

  return async function submitFinaliseProject() {
    const projectTypeName = getProjectTypeName();
    try {
      renderCallout(
        finaliseStatus,
        "info",
        i18nStrings.creatingProjectFormat.replace("%(project_type)s", projectTypeName),
      );
      if (finaliseProjectBtn) finaliseProjectBtn.disabled = true;
      if (advancedOptionsToggle) advancedOptionsToggle.disabled = true;
      if (finaliseConfirmBtn) finaliseConfirmBtn.disabled = true;
      if (finaliseCancelBtn) finaliseCancelBtn.disabled = true;

      const customCreds = getCustomCreds();
      const finalizeSource = document.getElementById("finalize-source");
      const odkUrlHidden = document.getElementById("external_project_instance_url_hidden");
      const odkUserHidden = document.getElementById("external_project_username_hidden");
      const odkPassHidden = document.getElementById("external_project_password_hidden");
      const qfieldUrlHidden = document.getElementById("qfield_cloud_url_hidden");
      const qfieldUserHidden = document.getElementById("qfield_cloud_user_hidden");
      const qfieldPassHidden = document.getElementById("qfield_cloud_password_hidden");
      const qfieldOrgHidden = document.getElementById("qfield_cloud_org_hidden");

      if (finalizeSource) finalizeSource.value = customCreds ? "custom" : "default";

      if (odkUrlHidden) odkUrlHidden.value = "";
      if (odkUserHidden) odkUserHidden.value = "";
      if (odkPassHidden) odkPassHidden.value = "";
      if (qfieldUrlHidden) qfieldUrlHidden.value = "";
      if (qfieldUserHidden) qfieldUserHidden.value = "";
      if (qfieldPassHidden) qfieldPassHidden.value = "";
      if (qfieldOrgHidden) qfieldOrgHidden.value = "";

      if (customCreds) {
        if (isOdk) {
          if (odkUrlHidden) odkUrlHidden.value = customCreds.url || "";
          if (odkUserHidden) odkUserHidden.value = customCreds.username || "";
          if (odkPassHidden) odkPassHidden.value = customCreds.password || "";
        } else if (isQField) {
          if (qfieldUrlHidden) qfieldUrlHidden.value = customCreds.url || "";
          if (qfieldUserHidden) qfieldUserHidden.value = customCreds.username || "";
          if (qfieldPassHidden) qfieldPassHidden.value = customCreds.password || "";
          if (qfieldOrgHidden) qfieldOrgHidden.value = customCreds.org || "";
        }
      }

      const finaliseFormPostUrl = finaliseForm.getAttribute("hx-post");
      if (!finaliseFormPostUrl) {
        throw new Error("Finalise endpoint not configured");
      }

      await htmx.ajax("POST", finaliseFormPostUrl, {
        source: finaliseForm,
        target: "#finalise-status",
        swap: "innerHTML",
        values: {},
      });

      if (finaliseProjectBtn) finaliseProjectBtn.disabled = false;
      if (advancedOptionsToggle) advancedOptionsToggle.disabled = false;
    } catch (error) {
      renderCallout(finaliseStatus, "danger", `${i18nStrings.errorPrefix} ${error.message}`);
      if (finaliseProjectBtn) finaliseProjectBtn.disabled = false;
      if (advancedOptionsToggle) advancedOptionsToggle.disabled = false;
    } finally {
      if (finaliseConfirmBtn) finaliseConfirmBtn.disabled = false;
      if (finaliseCancelBtn) finaliseCancelBtn.disabled = false;
    }
  };
}
