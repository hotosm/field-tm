import { LoginStateTypes } from '@/store/types/ILogin';
import { createSlice } from '@reduxjs/toolkit';

const initialState: LoginStateTypes = {
  authDetails: null,
  loginModalOpen: false,
};

const LoginSlice = createSlice({
  name: 'login',
  initialState: initialState,
  reducers: {
    setAuthDetails(state, action) {
      state.authDetails = action.payload;
    },
    signOut(state) {
      state.authDetails = null;
    },
    setLoginModalOpen(state, action) {
      state.loginModalOpen = action.payload;
    },
  },
});

export const LoginActions = LoginSlice.actions;
export default LoginSlice;
