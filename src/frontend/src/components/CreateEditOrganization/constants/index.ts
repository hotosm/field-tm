import { radioOptionsType } from '@/models/organisation/organisationModel';

export const organizationTypeOptions: radioOptionsType[] = [
  { name: 'osm_community', value: 'OSM_COMMUNITY', label: 'OSM Community' },
  { name: 'company', value: 'COMPANY', label: 'Company' },
  { name: 'non_profit', value: 'NON_PROFIT', label: 'Non-profit' },
  { name: 'university', value: 'UNIVERSITY', label: 'University' },
  { name: 'other', value: 'OTHER', label: 'Other' },
];

export const odkTypeOptions: radioOptionsType[] = [
  { name: 'odk_server_type', value: 'OWN', label: 'Use your own ODK server' },
  { name: 'odk_server_type', value: 'HOT', label: "Request HOT's ODK server" },
];
