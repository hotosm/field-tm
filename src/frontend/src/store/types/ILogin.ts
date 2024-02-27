export type LoginType = {
  loginToken: logintTokenType | {};
  authDetails: {} | string;
};

type logintTokenType = {
  id: string;
  osm_oauth_token: string;
  picture: string;
  role: string;
  sessionToken: string | null;
  username: string;
};
