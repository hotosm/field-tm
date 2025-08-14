// PAYLOAD TYPES

// PARAMS TYPES
export type getUserListParamsType = {
  search: string;
  signin_type?: 'osm' | 'google';
};

// RESPONSE TYPES
export type getUserListType = {
  sub: string;
  username: string;
};
