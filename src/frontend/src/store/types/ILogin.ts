export type LoginStateTypes = {
  authDetails: authDetailsType | null;
  loginModalOpen: false;
};

type authDetailsType = {
  id: string;
  picture: string;
  role: string;
  username: string;
  // sessionToken: string | null;
};
