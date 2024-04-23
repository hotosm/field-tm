export type LoginStateTypes = {
  loginToken: logintTokenType | {};
  authDetails: {} | string;
  loginModalOpen: false;
};

type logintTokenType = {
  id: string;
  osm_oauth_token: string;
  picture: string;
  role: string;
  sessionToken: string | null;
  username: string;
};
