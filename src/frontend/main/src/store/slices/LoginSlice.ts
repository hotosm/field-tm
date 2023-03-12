
import CoreModules from "../../shared/CoreModules";

const LoginSlice = CoreModules.createSlice({
    name: 'login',
    initialState: {
        loginProjectSummary: [],
        loginToken: [],
        loginProjectLoading: true,
        loginId: null,
    },
    reducers: {
        SetLoginProjectSummary(state, action) {
            state.loginProjectSummary = action.payload
        },
        LoginProjectLoading(state, action) {
            state.loginProjectLoading = action.payload
        },
        SetLoginId(state, action) {
            state.loginId = action.payload
        },
        SetLoginToken(state, action) {
            state.loginToken = action.payload
        }
    }
})


export const LoginActions = LoginSlice.actions;
export default LoginSlice;
