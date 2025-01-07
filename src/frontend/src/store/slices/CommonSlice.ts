import { createSlice, PayloadAction } from '@reduxjs/toolkit';
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
    SetSnackBar(state, action: PayloadAction<CommonStateTypes['snackbar']>) {
      state.snackbar = action.payload;
    },
    SetLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload;
    },
    PostOrganisationLoading(state, action: PayloadAction<boolean>) {
      state.postOrganisationLoading = action.payload;
    },
    SetCurrentStepFormStep(state, action: PayloadAction<{ flag: string; step: number }>) {
      state.currentStepFormStep[action.payload.flag] = { step: action.payload.step };
    },
    SetProjectNotFound(state, action: PayloadAction<boolean>) {
      state.projectNotFound = action.payload;
    },
  },
});

export const CommonActions = CommonSlice.actions;
export default CommonSlice;
