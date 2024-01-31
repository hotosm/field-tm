import { createSlice } from '@reduxjs/toolkit';
import { SubmissionStateTypes } from '@/store/types/ISubmissions';

const initialState: SubmissionStateTypes = {
  submissionDetailsLoading: true,
  submissionDetails: [],
  submissionInfographics: [],
  submissionInfographicsLoading: false,
  submissionContributors: [],
  submissionContributorsLoading: true,
  submissionFormFields: [],
  submissionTableData: [],
  submissionFormFieldsLoading: false,
  submissionTableDataLoading: false,
  submissionTableRefreshing: false,
  validatedVsMappedInfographics: [],
  validatedVsMappedLoading: false,
};

const SubmissionSlice = createSlice({
  name: 'submission',
  initialState: initialState,
  reducers: {
    SetSubmissionDetailsLoading(state, action) {
      state.submissionDetailsLoading = action.payload;
    },
    SetSubmissionDetails(state, action) {
      state.submissionDetails = action.payload;
    },
    SetSubmissionInfographics(state, action) {
      state.submissionInfographics = action.payload;
    },
    SetSubmissionInfographicsLoading(state, action) {
      state.submissionInfographicsLoading = action.payload;
    },
    SetValidatedVsMappedInfographics(state, action) {
      state.validatedVsMappedInfographics = action.payload;
    },
    SetValidatedVsMappedLoading(state, action) {
      state.validatedVsMappedLoading = action.payload;
    },
    SetSubmissionContributors(state, action) {
      state.submissionContributors = action.payload;
    },
    SetSubmissionContributorsLoading(state, action) {
      state.submissionContributorsLoading = action.payload;
    },
    SetSubmissionFormFields(state, action) {
      state.submissionFormFields = action.payload;
    },
    SetSubmissionTable(state, action) {
      state.submissionTableData = action.payload;
    },
    SetSubmissionFormFieldsLoading(state, action) {
      state.submissionFormFieldsLoading = action.payload;
    },
    SetSubmissionTableLoading(state, action) {
      state.submissionTableDataLoading = action.payload;
    },
    SetSubmissionTableRefreshing(state, action) {
      state.submissionTableRefreshing = action.payload;
    },
  },
});

export const SubmissionActions = SubmissionSlice.actions;
export default SubmissionSlice;
