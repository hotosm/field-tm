import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { UserStateTypes } from '@/store/types/IUser';

export const initialState: UserStateTypes = {
  userList: [],
  userListLoading: false,
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
  },
});

export const UserActions = UserSlice.actions;
export default UserSlice;
