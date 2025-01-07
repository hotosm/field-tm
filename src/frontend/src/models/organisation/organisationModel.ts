export interface OrganisationModal {
  name: string;
  description: string;
  url: string;
  type: number;
}

export interface FormCategoryListModel {
  id: number;
  title: string;
}
export interface OrganisationListModel {
  name: string;
  slug: string;
  description: string;
  type: number;
  id: number;
  logo: string;
  url: string;
}

export interface GetOrganisationDataModel {
  name: string;
  slug: string;
  description: string;
  type: number;
  id: number;
  logo: string | null;
  url: string;
  approved: boolean;
  odk_central_url: string | null;
}

export type organizationTypeOptionsType = {
  name: string;
  value: string;
  label: string;
};

export type consentDetailsFormDataType = {
  give_consent: '' | 'yes' | 'no';
  review_documentation: string[];
  log_into: string[];
  participated_in: string[];
};
