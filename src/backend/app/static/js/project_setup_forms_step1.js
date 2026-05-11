import {
  OSM_FORM_TITLE_TO_PRESET,
  bindAdvancedToggle,
  parseSetupPreference,
  presetForFormTitle,
  renderCallout,
  saveSetupPreference,
} from "./project_setup_shared.js";

export function initProjectSetupFormSelection({
  i18nStrings,
  setupPreferenceKey,
  hasXlsform,
  initialFormTemplates,
}) {
  const uploadXlsformBtn = document.getElementById("upload-xlsform-btn");
  const formAdvancedConfigToggle = document.getElementById("form-advanced-config-toggle");
  const formAdvancedConfigPanel = document.getElementById("form-advanced-config-panel");
  const uploadXlsformForm = document.getElementById("upload-xlsform-form");
  const uploadXlsformSubmitBtn = document.getElementById("upload-xlsform-submit-btn");
  const selectedXlsformName = document.getElementById("selected-xlsform-name");
  const xlsformFileInput = document.getElementById("xlsform-file-input");
  const xlsformSelect = document.getElementById("xlsform-select");
  const xlsformStatus = document.getElementById("xlsform-status");
  const templateFormIdInput = document.getElementById("template-form-id");
  const formTemplatesById = new Map();

  bindAdvancedToggle(formAdvancedConfigToggle, formAdvancedConfigPanel);

  const includePhotoCheckbox = document.getElementById("include-photo-upload-checkbox");
  const mandatoryPhotoCheckbox = document.getElementById("mandatory-photo-checkbox");
  const mandatoryPhotoLabel = document.getElementById("mandatory-photo-label");
  const includePhotoHidden = document.getElementById("include-photo-upload-hidden");
  const verificationFieldsCheckbox = document.getElementById("verification-fields-checkbox");
  const needVerificationHidden = document.getElementById("need-verification-fields-hidden");
  const customFormDisclaimer = document.getElementById("custom-form-disclaimer");

  if (includePhotoCheckbox && mandatoryPhotoCheckbox && mandatoryPhotoLabel) {
    includePhotoCheckbox.addEventListener("change", function () {
      const enabled = includePhotoCheckbox.checked;
      mandatoryPhotoCheckbox.disabled = !enabled;
      mandatoryPhotoLabel.style.opacity = enabled ? "1" : "0.4";
      if (!enabled) mandatoryPhotoCheckbox.checked = false;
      if (includePhotoHidden) includePhotoHidden.value = enabled ? "true" : "false";
    });
  }

  if (verificationFieldsCheckbox && needVerificationHidden) {
    verificationFieldsCheckbox.addEventListener("change", function () {
      needVerificationHidden.value = verificationFieldsCheckbox.checked ? "true" : "false";
    });
  }

  const defaultLanguageSelect = document.getElementById("default-language-select");
  const defaultLanguageExplicitHidden = document.getElementById("default-language-explicit-hidden");
  if (defaultLanguageSelect) {
    const localeToLanguage = {
      en: "english",
      es: "spanish",
      fr: "french",
      pt: "portuguese",
      pt_br: "portuguese",
      sw: "swahili",
      hi: "hindi",
    };
    const htmlLang = document.documentElement.lang || "";
    const matched = localeToLanguage[htmlLang] || localeToLanguage[htmlLang.split(/[-_]/)[0]];
    if (matched && defaultLanguageSelect.querySelector(`option[value="${matched}"]`)) {
      defaultLanguageSelect.value = matched;
    }

    defaultLanguageSelect.addEventListener("change", function () {
      if (defaultLanguageExplicitHidden) defaultLanguageExplicitHidden.value = "true";
    });
  }

  function setStep1Status(message, variant = "info") {
    if (!xlsformStatus) return;
    renderCallout(xlsformStatus, variant, message);
  }

  function setStep1Ready(isReady) {
    if (!uploadXlsformSubmitBtn) return;
    uploadXlsformSubmitBtn.disabled = !isReady;
  }

  function clearTemplateSelection() {
    if (templateFormIdInput) templateFormIdInput.value = "";
  }

  function setSurveyTypeOptions(forms) {
    if (!xlsformSelect) return;
    xlsformSelect.innerHTML = "";

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = i18nStrings.selectSurveyTypePlaceholder;
    xlsformSelect.appendChild(placeholder);

    forms.forEach((form) => {
      const option = document.createElement("option");
      option.value = String(form.id);
      option.textContent = form.title;
      xlsformSelect.appendChild(option);
    });
  }

  function loadSurveyTypes() {
    if (!xlsformSelect) return;
    xlsformSelect.disabled = true;

    formTemplatesById.clear();
    initialFormTemplates.forEach((form) => formTemplatesById.set(String(form.id), form));

    if (initialFormTemplates.length === 0) {
      xlsformSelect.innerHTML = `<option value="">${i18nStrings.noSurveyTypesAvailable}</option>`;
      setStep1Status(i18nStrings.noSurveyFormsAvailable, "warning");
      return;
    }

    setSurveyTypeOptions(initialFormTemplates);
    xlsformSelect.disabled = false;
    setStep1Status(i18nStrings.selectSurveyTypeOrUpload, "info");
  }

  if (!hasXlsform) {
    setStep1Ready(false);
    loadSurveyTypes();
  }

  if (xlsformSelect && !hasXlsform) {
    xlsformSelect.addEventListener("change", function () {
      const formId = xlsformSelect.value;
      if (!formId) {
        clearTemplateSelection();
        setStep1Ready(false);
        return;
      }

      if (templateFormIdInput) templateFormIdInput.value = formId;
      if (xlsformFileInput) xlsformFileInput.value = "";
      if (selectedXlsformName) selectedXlsformName.textContent = "";
      if (customFormDisclaimer) customFormDisclaimer.style.display = "none";

      const selectedForm = formTemplatesById.get(String(formId));
      const preset = presetForFormTitle(selectedForm?.title);
      saveSetupPreference(setupPreferenceKey, {
        mode: "template",
        templateFormId: formId,
        templateTitle: selectedForm?.title || null,
        category: preset.category,
        geomType: preset.geomType,
        centroid: preset.centroid,
      });

      setStep1Ready(true);
      setStep1Status(i18nStrings.surveyTypeSelected, "info");
    });
  }

  if (uploadXlsformBtn && xlsformFileInput && !hasXlsform) {
    uploadXlsformBtn.addEventListener("click", () => {
      xlsformFileInput.click();
    });

    xlsformFileInput.addEventListener("change", function (e) {
      const file = e.target.files[0];
      if (!file) return;

      const validExtensions = [".xls", ".xlsx"];
      const fileExtension = "." + file.name.split(".").pop().toLowerCase();
      if (!validExtensions.includes(fileExtension)) {
        setStep1Status(i18nStrings.invalidXlsformFileType, "danger");
        xlsformFileInput.value = "";
        setStep1Ready(false);
        return;
      }

      clearTemplateSelection();
      if (xlsformSelect) xlsformSelect.value = "";
      if (selectedXlsformName) {
        selectedXlsformName.textContent = `${i18nStrings.selectedFilePrefix} ${file.name}`;
      }
      if (customFormDisclaimer) customFormDisclaimer.style.display = "block";

      saveSetupPreference(setupPreferenceKey, {
        mode: "custom",
        templateFormId: null,
        templateTitle: null,
        category: "buildings",
        geomType: "POLYGON",
        centroid: false,
      });

      setStep1Ready(true);
      setStep1Status(i18nStrings.customFormSelected, "info");
    });
  }

  if (uploadXlsformForm && !hasXlsform) {
    uploadXlsformForm.addEventListener("submit", function (e) {
      const hasTemplateSelection = Boolean(templateFormIdInput?.value);
      const hasUploadedFile = Boolean(xlsformFileInput?.files?.length);

      if (!hasTemplateSelection && !hasUploadedFile) {
        e.preventDefault();
        setStep1Status(i18nStrings.chooseSurveyTypeFirst, "warning");
        setStep1Ready(false);
        return false;
      }
    });
  }

  return {
    mapCategoryToTitle(category) {
      return Object.keys(OSM_FORM_TITLE_TO_PRESET).find(
        (title) => OSM_FORM_TITLE_TO_PRESET[title]?.category === category,
      );
    },
    persistDownloadPreference(config) {
      const preference = parseSetupPreference(setupPreferenceKey) || {};
      saveSetupPreference(setupPreferenceKey, {
        ...preference,
        mode: preference.mode || "template",
        category: config.category,
        geomType: config.geomType,
        centroid: config.centroid,
      });
    },
  };
}
