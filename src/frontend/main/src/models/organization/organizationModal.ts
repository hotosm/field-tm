
export interface OrganizationModal {
    name: string,
    description: string,
    url: string,
    type: number,
}

  export interface FormCategoryListModel {
    id: number,
    title: string,
  }
  export interface OrganisationListModel {
    name: string;
    slug: string;
    description: string;
    type: number;
    subscription_tier: null | string;
    id: number;
    logo: string;
    url: string;
  }