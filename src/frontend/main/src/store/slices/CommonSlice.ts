
import CoreModules from "../../shared/CoreModules";
const CommonSlice = CoreModules.createSlice({
    name: 'common',
    initialState: {
        snackbar: {
            open: false,
            message: '',
            variant: 'info',
            duration: 0
        },
        loading:false,
        postOrganizationLoading:false
    },
    reducers: {
        SetSnackBar(state, action) {
            state.snackbar = action.payload
        },
        SetLoading(state,action){
            state.loading = action.payload
        },
        PostOrganizationLoading(state,action){
            state.organization = action.payload
        }
    }
})


export const CommonActions = CommonSlice.actions;
export default CommonSlice;
