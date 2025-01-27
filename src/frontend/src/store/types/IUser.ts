import { userType } from '@/models/user/userModel';

export type UserStateTypes = {
  userList: userType[];
  userListLoading: boolean;
};
