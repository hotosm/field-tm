import { projectUserInvites, userType } from '@/models/user/userModel';

export type UserStateTypes = {
  updateUserRoleLoading: boolean;
  getUserNamesLoading: boolean;
  userNames: Pick<userType, 'sub' | 'username'>[];
  inviteNewUserPending: boolean;
  getProjectUserInvitesLoading: boolean;
  projectUserInvitesList: projectUserInvites[];
  projectUserInvitesError: string[];
};
