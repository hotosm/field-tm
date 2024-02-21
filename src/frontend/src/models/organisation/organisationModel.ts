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
  logo: string;
  url: string;
  approved: boolean;
}
