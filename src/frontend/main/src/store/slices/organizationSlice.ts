import CoreModules from "../../shared/CoreModules.js"

const OrganizationSlice = CoreModules.createSlice({
    name : 'organization',
    initialState : {
        organizationData : [],
        postOrganizationData : [],
        organizationDataLoading: false,
        postOrganizationDataLoading: false,
    },
    reducers : {
        GetOrganizationsData(state, action){
            state.oraganizationData=action.payload
        },
        GetOrganizationDataLoading(state, action){
            state.organizationDataLoading=action.payload
        },
        postOrganizationData(state, action){
            state.postOrganizationData=action.payload
        },
        PostOrganizationDataLoading(state, action){
            state.postOrganizationDataLoading=action.payload
        },
    }
})

export const OrganizationAction =  OrganizationSlice.actions;
export default OrganizationSlice;