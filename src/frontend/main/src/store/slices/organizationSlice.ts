import CoreModules from "../../shared/CoreModules.js"

const OrganizationSlice = CoreModules.createSlice({
    name: 'organization',
    initialState: {
        organizationFormData:{},
        organizationData: [],
        postOrganizationData: null,
        organizationDataLoading: false,
        postOrganizationDataLoading: false,
    },
    reducers: {
        GetOrganizationsData(state, action) {
            state.oraganizationData = action.payload
        },
        GetOrganizationDataLoading(state, action) {
            state.organizationDataLoading = action.payload
        },
        postOrganizationData(state, action) {
            state.postOrganizationData = action.payload
        },
        PostOrganizationDataLoading(state, action) {
            state.postOrganizationDataLoading = action.payload
        },
        SetOrganizationFormData(state, action) {
            state.organizationFormData = action.payload
        },
    }
})

export const OrganizationAction = OrganizationSlice.actions;
export default OrganizationSlice;