
import CoreModules from "../../shared/CoreModules";
import storage from 'redux-persist/lib/storage';
const LoginSlice = CoreModules.createSlice({
    name: 'login',
    initialState: {
        loginToken: null,
    },
    reducers: {
        SetLoginToken(state, action) {
            state.loginToken = action.payload
        },
        signOut(state,action) {
            storage.removeItem('persist:login')
            state.loginToken = action.payload
        },
     
    }
})


export const LoginActions = LoginSlice.actions;
export default LoginSlice;
