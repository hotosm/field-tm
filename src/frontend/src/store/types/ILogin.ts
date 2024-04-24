export type LoginStateTypes = {
  authDetails: authDetailsType | null;
  loginModalOpen: false;
};

type authDetailsType = {
  id: string;
  img_url: string;
  role: string;
  username: string;
  // sessionToken: string | null;
};
