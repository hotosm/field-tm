import { project_roles } from '@/types/enums';

export type invitePropType = {
  roleList: {
    id: string;
    value: project_roles;
    label: string;
  }[];
};

export const inviteOptions = [
  {
    name: 'invite_options',
    value: 'osm',
    label: 'Invite via OSM',
  },
  {
    name: 'invite_options',
    value: 'gmail',
    label: 'Invite via Gmail',
  },
];
