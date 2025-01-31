import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { UserStateTypes } from '@/store/types/IUser';
import { userType } from '@/models/user/userModel';

export const initialState: UserStateTypes = {
  userList: {
    results: [],
    pagination: {
      has_next: false,
      has_prev: false,
      next_num: null,
      page: 1,
      pages: null,
      prev_num: null,
      per_page: 13,
      total: null,
    },
  },
  userListLoading: false,
  updateUserRoleLoading: false,
  userListForSelect: [],
  userListForSelectLoading: false,
};

const UserSlice = createSlice({
  name: 'user',
  initialState: initialState,
  reducers: {
    SetUserList: (state, action: PayloadAction<UserStateTypes['userList']>) => {
      state.userList = action.payload;
    },
    SetUserListLoading: (state, action: PayloadAction<boolean>) => {
      state.userListLoading = action.payload;
    },
    UpdateUserList: (state, action: PayloadAction<userType>) => {
      state.userList.results = state.userList.results.map((user) =>
        user.id === action.payload.id ? action.payload : user,
      );
    },
    SetUpdateUserRoleLoading: (state, action: PayloadAction<boolean>) => {
      state.updateUserRoleLoading = action.payload;
    },
    SetUserListForSelect: (state, action: PayloadAction<UserStateTypes['userListForSelect']>) => {
      state.userListForSelect = action.payload;
    },
    SetUserListForSelectLoading: (state, action: PayloadAction<boolean>) => {
      state.userListLoading = action.payload;
    },
  },
});

export const UserActions = UserSlice.actions;
export default UserSlice;
