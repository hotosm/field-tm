import CoreModules from '../../shared/CoreModules.js';

const OrganisationSlice = CoreModules.createSlice({
  name: 'organisation',
  initialState: {
    organisationFormData: {},
    organisationData: [],
    postOrganisationData: null,
    organisationDataLoading: false,
    postOrganisationDataLoading: false,
  },
  reducers: {
    GetOrganisationsData(state, action) {
      state.oraganizationData = action.payload;
    },
    GetOrganisationDataLoading(state, action) {
      state.organisationDataLoading = action.payload;
    },
    postOrganisationData(state, action) {
      state.postOrganisationData = action.payload;
    },
    PostOrganisationDataLoading(state, action) {
      state.postOrganisationDataLoading = action.payload;
    },
    SetOrganisationFormData(state, action) {
      state.organisationFormData = action.payload;
    },
  },
});

export const OrganisationAction = OrganisationSlice.actions;
export default OrganisationSlice;
