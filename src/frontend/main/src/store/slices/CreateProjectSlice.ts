import CoreModules from "../../shared/CoreModules";


const CreateProject = CoreModules.createSlice({
    name: 'createproject',
    initialState: {
        projectDetails:{},
        projectDetailsResponse:null,
        projectDetailsLoading:false,
        projectArea:null,
        projectAreaLoading:false,
        formCategoryList:null,
    },
    reducers: {
        SetProjectDetails(state, action) {
            state.projectDetails = {...state.projectDetails,[action.payload.key]:action.payload.value}
        },
        CreateProjectLoading(state, action) {
            state.projectDetailsLoading = action.payload
        },
        PostProjectDetails(state, action) {
            state.projectDetailsResponse = action.payload
        },
        ClearCreateProjectFormData(state, action) {
            state.projectDetailsResponse = null
            state.projectDetails = {}
            state.projectArea = null
        },
        UploadAreaLoading(state, action) {
            state.projectAreaLoading = action.payload
        },
        PostUploadAreaSuccess(state, action) {
            state.projectArea = action.payload
        },
        GetFormCategoryLoading(state, action) {
            state.formCategoryLoading = action.payload
        },
        GetFormCategoryList(state, action) {
            state.formCategoryList = action.payload
        },
        SetFormCategory(state, action) {
            state.formCategoryList = action.payload
        },
    }
})


export const CreateProjectActions = CreateProject.actions;
export default CreateProject;