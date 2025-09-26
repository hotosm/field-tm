import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { UserStateTypes } from '@/store/types/IUser';

export const initialState: UserStateTypes = {
  updateUserRoleLoading: false,
  userNames: [],
  getProjectUserInvitesLoading: false,
  projectUserInvitesList: [],
  getUserNamesLoading: false,
  inviteNewUserPending: false,
  projectUserInvitesError: [],
};

const UserSlice = createSlice({
  name: 'user',
  initialState: initialState,
  reducers: {
    SetUpdateUserRoleLoading: (state, action: PayloadAction<boolean>) => {
      state.updateUserRoleLoading = action.payload;
    },
    SetUserNames: (state, action: PayloadAction<UserStateTypes['userNames']>) => {
      state.userNames = action.payload;
    },
    GetUserNamesLoading: (state, action: PayloadAction<boolean>) => {
      state.getUserNamesLoading = action.payload;
    },
    InviteNewUserPending: (state, action: PayloadAction<boolean>) => {
      state.inviteNewUserPending = action.payload;
    },
    SetProjectUserInvites: (state, action: PayloadAction<UserStateTypes['projectUserInvitesList']>) => {
      state.projectUserInvitesList = action.payload;
    },
    GetProjectUserInvitesLoading: (state, action: PayloadAction<boolean>) => {
      state.getProjectUserInvitesLoading = action.payload;
    },
    SetProjectUserInvitesError: (state, action: PayloadAction<string[]>) => {
      state.projectUserInvitesError = action.payload;
    },
  },
});

export const UserActions = UserSlice.actions;
export default UserSlice;
