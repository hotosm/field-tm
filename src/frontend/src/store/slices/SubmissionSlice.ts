import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { SubmissionStateTypes } from '@/store/types/ISubmissions';
import { validatedMappedType } from '@/models/submission/submissionModel';

const initialState: SubmissionStateTypes = {
  submissionContributors: [],
  submissionContributorsLoading: false,
  updateReviewStatusModal: {
    toggleModalStatus: false,
    instanceId: null,
    taskId: null,
    projectId: null,
    reviewState: '',
    taskUid: null,
    entity_id: null,
    label: null,
  },
  updateReviewStateLoading: false,
  mappedVsValidatedTask: [],
  mappedVsValidatedTaskLoading: false,
};

const SubmissionSlice = createSlice({
  name: 'submission',
  initialState: initialState,
  reducers: {
    SetSubmissionContributors(state, action: PayloadAction<SubmissionStateTypes['submissionContributors']>) {
      state.submissionContributors = action.payload;
    },
    SetSubmissionContributorsLoading(state, action: PayloadAction<boolean>) {
      state.submissionContributorsLoading = action.payload;
    },
    SetUpdateReviewStatusModal(state, action: PayloadAction<SubmissionStateTypes['updateReviewStatusModal']>) {
      state.updateReviewStatusModal = action.payload;
    },
    UpdateReviewStateLoading(state, action: PayloadAction<boolean>) {
      state.updateReviewStateLoading = action.payload;
    },
    SetMappedVsValidatedTask(state, action: PayloadAction<validatedMappedType[]>) {
      const MappedVsValidatedTask = action.payload;
      state.mappedVsValidatedTask = MappedVsValidatedTask?.map((task) => ({
        ...task,
        label: task?.date?.split('/').slice(0, 2).join('/'),
      }));
    },
    SetMappedVsValidatedTaskLoading(state, action: PayloadAction<boolean>) {
      state.mappedVsValidatedTaskLoading = action.payload;
    },
  },
});

export const SubmissionActions = SubmissionSlice.actions;
export default SubmissionSlice;
