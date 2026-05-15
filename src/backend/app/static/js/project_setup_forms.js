import { initProjectSetupDataExtract } from "./project_setup_forms_step2.js";
import { initProjectSetupFormSelection } from "./project_setup_forms_step1.js";

export function initProjectSetupForms({
  i18nStrings,
  projectId,
  hasXlsform,
  initialFormTemplates,
}) {
  const setupPreferenceKey = `ftm-project-setup-preference-${projectId}`;

  const step1 = initProjectSetupFormSelection({
    i18nStrings,
    setupPreferenceKey,
    hasXlsform,
    initialFormTemplates,
  });

  initProjectSetupDataExtract({
    i18nStrings,
    projectId,
    hasXlsform,
    setupPreferenceKey,
    mapCategoryToTitle: step1.mapCategoryToTitle,
    persistDownloadPreference: step1.persistDownloadPreference,
  });
}
