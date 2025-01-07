// import CoreModules from '@/shared/CoreModules.js';
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { IOrganisationState } from '@/store/types/IOrganisation';

export const initialState: IOrganisationState = {
  organisationFormData: {},
  organisationData: [],
  myOrganisationData: [],
  postOrganisationData: null,
  organisationDataLoading: false,
  myOrganisationDataLoading: false,
  postOrganisationDataLoading: false,
  consentDetailsFormData: {
    give_consent: '',
    review_documentation: [],
    log_into: [],
    participated_in: [],
  },
  consentApproval: false,
  organizationApprovalStatus: {
    isSuccess: false,
    organizationApproving: false,
    organizationRejecting: false,
  },
};

const OrganisationSlice = createSlice({
  name: 'organisation',
  initialState: initialState,
  reducers: {
    GetOrganisationsData(state, action: PayloadAction<IOrganisationState['organisationData']>) {
      state.organisationData = action.payload;
    },
    GetOrganisationDataLoading(state, action: PayloadAction<boolean>) {
      state.organisationDataLoading = action.payload;
    },
    GetMyOrganisationsData(state, action: PayloadAction<IOrganisationState['myOrganisationData']>) {
      state.myOrganisationData = action.payload;
    },
    GetMyOrganisationDataLoading(state, action: PayloadAction<boolean>) {
      state.myOrganisationDataLoading = action.payload;
    },
    postOrganisationData(state, action: PayloadAction<IOrganisationState['postOrganisationData']>) {
      state.postOrganisationData = action.payload;
    },
    PostOrganisationDataLoading(state, action: PayloadAction<boolean>) {
      state.postOrganisationDataLoading = action.payload;
    },
    SetOrganisationFormData(state, action: PayloadAction<IOrganisationState['organisationFormData']>) {
      state.organisationFormData = action.payload;
    },
    SetConsentDetailsFormData(state, action: PayloadAction<IOrganisationState['consentDetailsFormData']>) {
      state.consentDetailsFormData = action.payload;
    },
    SetConsentApproval(state, action: PayloadAction<boolean>) {
      state.consentApproval = action.payload;
    },
    SetIndividualOrganization(state, action: PayloadAction<IOrganisationState['organisationFormData']>) {
      state.organisationFormData = action.payload;
    },
    SetOrganizationApproving(state, action: PayloadAction<boolean>) {
      state.organizationApprovalStatus.organizationApproving = action.payload;
    },
    SetOrganizationRejecting(state, action: PayloadAction<boolean>) {
      state.organizationApprovalStatus.organizationRejecting = action.payload;
    },
    SetOrganizationApprovalStatus(state, action: PayloadAction<boolean>) {
      state.organizationApprovalStatus.isSuccess = action.payload;
    },
  },
});

export const OrganisationAction = OrganisationSlice.actions;
export default OrganisationSlice;
