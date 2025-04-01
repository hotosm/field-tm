export type LoginStateTypes = {
  authDetails: authDetailsType | null;
  loginModalOpen: false;
};

type authDetailsType = {
  sub: string;
  username: string;
  profile_img: string | null;
  picture: string | null;
  email: string | null;
  role: string;
  project_roles: Record<string, any> | null;
  orgs_managed: number[] | null;
  // sessionToken: string | null;
};
