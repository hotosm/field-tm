interface IConsentDetailsFormData {
  give_consent: string;
  review_documentation: [];
  log_into: [];
  participated_in: [];
}

interface ValidationErrors {
  give_consent?: string;
  review_documentation?: string;
  log_into?: string;
  participated_in?: string;
}

function ConsentDetailsValidation(values: IConsentDetailsFormData) {
  const errors: ValidationErrors = {};

  if (!values?.give_consent) {
    errors.give_consent = 'Consent is required.';
  }
  if (values?.give_consent === 'no') {
    errors.give_consent = 'To proceed, it is required that you provide consent.';
  }
  if (values?.review_documentation?.length < 3) {
    errors.review_documentation = 'Please ensure that all checkboxes are marked.';
  }
  if (values?.log_into?.length < 1) {
    errors.log_into = 'Please ensure that any one of the checkbox is marked.';
  }

  return errors;
}

export default ConsentDetailsValidation;
