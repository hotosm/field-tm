// import CoreModules from '@/shared/CoreModules.js';
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { IOrganisationState } from '@/store/types/IOrganisation';

export const initialState: IOrganisationState = {
  consentDetailsFormData: {
    give_consent: '',
    review_documentation: [],
    log_into: [],
    participated_in: [],
  },
  consentApproval: false,
  organizationDeleteLoading: false,
  getOrganizationAdminsLoading: false,
  organizationAdmins: [],
  addOrganizationAdminPending: false,
};

const OrganisationSlice = createSlice({
  name: 'organisation',
  initialState: initialState,
  reducers: {
    SetConsentDetailsFormData(state, action: PayloadAction<IOrganisationState['consentDetailsFormData']>) {
      state.consentDetailsFormData = action.payload;
    },
    SetConsentApproval(state, action: PayloadAction<boolean>) {
      state.consentApproval = action.payload;
    },
    SetOrganizationDeleting(state, action: PayloadAction<boolean>) {
      state.organizationDeleteLoading = action.payload;
    },
    GetOrganizationAdminsLoading(state, action: PayloadAction<boolean>) {
      state.getOrganizationAdminsLoading = action.payload;
    },
    SetOrganizationAdmins(state, action: PayloadAction<IOrganisationState['organizationAdmins']>) {
      state.organizationAdmins = action.payload;
    },
    SetAddOrganizationAdminPending(state, action: PayloadAction<boolean>) {
      state.addOrganizationAdminPending = action.payload;
    },
  },
});

export const OrganisationAction = OrganisationSlice.actions;
export default OrganisationSlice;
