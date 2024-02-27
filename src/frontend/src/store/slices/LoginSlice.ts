import CoreModules from '@/shared/CoreModules';
import storage from 'redux-persist/lib/storage';
import { LoginStateTypes } from '@/store/types/ILogin';

const initialState: LoginStateTypes = {
  loginToken: {},
  authDetails: {},
};

const LoginSlice = CoreModules.createSlice({
  name: 'login',
  initialState: initialState,
  reducers: {
    SetLoginToken(state, action) {
      state.loginToken = action.payload;
    },
    signOut(state, action) {
      storage.removeItem('persist:login');
      state.loginToken = action.payload;
    },
    setAuthDetails(state, action) {
      state.authDetails = action.payload;
    },
  },
});

export const LoginActions = LoginSlice.actions;
export default LoginSlice;
