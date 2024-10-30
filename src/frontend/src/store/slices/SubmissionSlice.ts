import { createSlice } from '@reduxjs/toolkit';
import { SubmissionStateTypes } from '@/store/types/ISubmissions';

const initialState: SubmissionStateTypes = {
  submissionDetailsLoading: true,
  submissionDetails: null,
  submissionContributors: [],
  submissionContributorsLoading: true,
  submissionFormFields: [],
  submissionTableData: {
    results: [],
    pagination: {
      total: null,
      page: null,
      prev_num: null,
      next_num: null,
      per_page: null,
      pages: null,
    },
  },
  submissionFormFieldsLoading: false,
  submissionTableDataLoading: false,
  submissionTableRefreshing: false,
  updateReviewStatusModal: {
    toggleModalStatus: false,
    instanceId: null,
    taskId: null,
    projectId: null,
    reviewState: '',
    taskUid: null,
  },
  updateReviewStateLoading: false,
  mappedVsValidatedTask: [],
  mappedVsValidatedTaskLoading: false,
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
    SetUpdateReviewStatusModal(state, action) {
      state.updateReviewStatusModal = action.payload;
    },
    UpdateReviewStateLoading(state, action) {
      state.updateReviewStateLoading = action.payload;
    },
    UpdateSubmissionTableDataReview(state, action) {
      const updatedSubmission = action.payload;

      // submission-instance table update
      if (state.submissionTableData.results.length > 0) {
        const updatedSubmissionDataList = state.submissionTableData.results.map((submissionData: any) => {
          if (updatedSubmission.instanceId === submissionData.meta.instanceID) {
            return {
              ...submissionData,
              __system: { ...submissionData.__system, reviewState: updatedSubmission.reviewState },
            };
          }
          return submissionData;
        });
        state.submissionTableData.results = updatedSubmissionDataList;
      }

      // submission-instance key value pair update
      if (state.submissionDetails) {
        state.submissionDetails = {
          ...state.submissionDetails,
          __system: { ...state.submissionDetails.__system, reviewState: updatedSubmission.reviewState },
        };
      }
    },
    SetMappedVsValidatedTask(state, action) {
      const MappedVsValidatedTask = action.payload;
      state.mappedVsValidatedTask = MappedVsValidatedTask?.map((task) => ({
        ...task,
        label: task?.date?.split('/').slice(0, 2).join('/'),
      }));
    },
    SetMappedVsValidatedTaskLoading(state, action) {
      state.mappedVsValidatedTaskLoading = action.payload;
    },
  },
});

export const SubmissionActions = SubmissionSlice.actions;
export default SubmissionSlice;
