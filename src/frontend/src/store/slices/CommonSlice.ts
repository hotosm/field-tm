import { createSlice } from '@reduxjs/toolkit';
import { CommonStateTypes } from '@/store/types/ICommon';

const initialState: CommonStateTypes = {
  snackbar: {
    open: false,
    message: '',
    variant: 'info',
    duration: 0,
  },
  loading: false,
  postOrganisationLoading: false,
  currentStepFormStep: {
    create_project: {
      step: 1,
    },
  },
  projectNotFound: false,
};

const CommonSlice = createSlice({
  name: 'common',
  initialState: initialState,
  reducers: {
    SetSnackBar(state, action) {
      state.snackbar = action.payload;
    },
    SetLoading(state, action) {
      state.loading = action.payload;
    },
    PostOrganisationLoading(state, action) {
      state.organisation = action.payload;
    },
    SetCurrentStepFormStep(state, action) {
      state.currentStepFormStep[action.payload.flag] = { step: action.payload.step };
    },
    SetProjectNotFound(state, action) {
      state.projectNotFound = action.payload;
    },
  },
});

export const CommonActions = CommonSlice.actions;
export default CommonSlice;
