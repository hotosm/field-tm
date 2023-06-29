import CoreModules from "../../shared/CoreModules";


const CreateProject = CoreModules.createSlice({
    name: 'createproject',
    initialState: {
        projectDetails: { dimension: 10 },
        projectDetailsResponse: null,
        projectDetailsLoading: false,
        projectArea: null,
        projectAreaLoading: false,
        formCategoryList: [],
        generateQrLoading: false,
        organizationList: [],
        organizationListLoading: false,
        generateQrSuccess: null,
        generateProjectLogLoading: false,
        generateProjectLog: null,
        createProjectStep: 1,
        dividedTaskLoading: false,
        dividedTaskGeojson: false,
    },
    reducers: {
        SetProjectDetails(state, action) {
            state.projectDetails = { ...state.projectDetails, [action.payload.key]: action.payload.value }
        },
        CreateProjectLoading(state, action) {
            state.projectDetailsLoading = action.payload
        },
        PostProjectDetails(state, action) {
            state.projectDetailsResponse = action.payload
        },
        ClearCreateProjectFormData(state) {
            // state.projectDetailsResponse = null
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
        SetIndividualProjectDetailsData(state, action) {
            state.projectDetails = action.payload
        },
        GenerateProjectQRLoading(state, action) {
            state.generateQrLoading = action.payload
        },
        GetOrganisationList(state, action) {
            state.organizationList = action.payload
        },
        GetOrganisationListLoading(state, action) {
            state.organizationListLoading = action.payload
        },
        GenerateProjectQRSuccess(state, action) {
            if (action.payload.status === 'SUCCESS') {
                state.generateQrSuccess = null
            } else {
                state.generateQrSuccess = action.payload
            }
        },
        SetGenerateProjectQRSuccess(state, action) {
            state.generateQrSuccess = action.payload
            
        },
        GenerateProjectLogLoading(state, action) {
            state.generateProjectLogLoading = action.payload
        },
        SetGenerateProjectLog(state, action) {
            state.generateProjectLog = action.payload
        },
        SetCreateProjectFormStep(state, action) {
            state.createProjectStep = action.payload
        },
        GetDividedTaskFromGeojsonLoading(state, action) {
            state.dividedTaskLoading = action.payload
        },
        SetDividedTaskGeojson(state, action) {
            state.dividedTaskGeojson = action.payload
        },
        SetDividedTaskFromGeojsonLoading(state, action) {
            state.dividedTaskLoading = action.payload
        },
    }
})


export const CreateProjectActions = CreateProject.actions;
export default CreateProject;