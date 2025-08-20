// PAYLOAD
export type createUpdateOrganisationPayloadType = {
  logo?: string;
  name: string;
  slug?: string;
  created_by?: string;
  community_type: string;
  description: string;
  associated_email: string;
  url: string;
  type?: string;
  odk_central_url?: string;
  odk_central_user?: string;
  odk_central_password?: string;
};

// PARAMS
export type createOrganisationParamsType = {
  request_odk_server: boolean;
  mapper?: boolean;
};

export type addNewOrganisationAdminParamsType = {
  user_sub: string;
  project_id?: number;
  org_id?: number;
};

export type approveOrganisationParamsType = {
  org_id: number;
  set_primary_org_odk_server: boolean;
  mapper?: boolean;
};

export type updateOrganisationParamsType = {
  org_id: number;
  project_id?: number;
};

export type removeOrganisationAdminParamsType = {
  project_id?: number;
  org_id?: number;
};

// RESPONSE
export type organisationType = {
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
};

export type organisationAdminType = {
  user_sub: string;
  username: string;
  profile_img: string;
};
