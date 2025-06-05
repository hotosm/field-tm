import { projectUserInvites, userType } from '@/models/user/userModel';
import { paginationType } from './ICommon';

export type UserStateTypes = {
  userList: { results: userType[]; pagination: paginationType };
  userListLoading: boolean;
  updateUserRoleLoading: boolean;
  userListForSelect: { sub: string; username: string }[];
  userListForSelectLoading: boolean;
  getUserNamesLoading: boolean;
  userNames: Pick<userType, 'sub' | 'username'>[];
  inviteNewUserPending: boolean;
  getProjectUserInvitesLoading: boolean;
  projectUserInvitesList: projectUserInvites[];
  projectUserInvitesError: string[];
};
