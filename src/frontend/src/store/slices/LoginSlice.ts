import CoreModules from '@/shared/CoreModules';
import storage from 'redux-persist/lib/storage';
import { LoginStateTypes } from '@/store/types/ILogin';

const initialState: LoginStateTypes = {
  authDetails: null,
  loginModalOpen: false,
};

const LoginSlice = CoreModules.createSlice({
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
