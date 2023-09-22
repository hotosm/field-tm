import { createSlice } from '@reduxjs/toolkit';

const SubmissionSlice = createSlice({
  name: 'submission',
  initialState: {
    submissionDetailsLoading: true,
    submissionDetails: [],
  },
  reducers: {
    SetSubmissionDetailsLoading(state, action) {
      state.submissionDetailsLoading = action.payload;
    },
    SetSubmissionDetails(state, action) {
      state.submissionDetails = action.payload;
    },
  },
});

export const SubmissionActions = SubmissionSlice.actions;
export default SubmissionSlice;
