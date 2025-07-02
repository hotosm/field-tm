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
  id: number;
  name: string;
  approved: boolean;
  type: string;
  community_type: string;
  logo: string | null;
  description: string;
  slug: string;
  url: string;
  associated_email: string;
  odk_central_url: string | null;
}

export type radioOptionsType = {
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

export type OrganizationAdminsModel = {
  user_sub: string;
  username: string;
  profile_img: string | null;
};
