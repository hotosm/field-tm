import CoreModules from "../../shared/CoreModules.js"

const OrganizationSlice = CoreModules.createSlice({
    name : 'organization',
    initialState : {
        organizationData : [],
        organizationDataLoading: false,
    },
    reducers : {
        GetOrganizationsData(state, action){
            state.oraganizationData=action.payload
        },
        GetOrganizationDataLoading(state, action){
            state.organizationDataLoading=action.payload
        }
    }
})

export const OrganizationAction =  OrganizationSlice.actions;
export default OrganizationSlice;