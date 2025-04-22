import { projectUserInvites, userType } from '@/models/user/userModel';
import { paginationType } from './ICommon';

export type UserStateTypes = {
  userList: { results: userType[]; pagination: paginationType };
  userListLoading: boolean;
  updateUserRoleLoading: boolean;
  userListForSelect: userType[];
  userListForSelectLoading: boolean;
  getUserNamesLoading: boolean;
  userNames: Pick<userType, 'sub' | 'username'>[];
  inviteNewUserPending: boolean;
  getProjectUserInvitesLoading: boolean;
  projectUserInvitesList: projectUserInvites[];
};
