import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { CommonStateTypes } from '@/store/types/ICommon';
import { selectOptionsType } from '@/components/common/Select2';

const initialState: CommonStateTypes = {
  snackbar: {
    open: false,
    message: '',
    variant: 'info',
    duration: 2000,
  },
  loading: false,
  postOrganisationLoading: false,
  projectNotFound: false,
  previousSelectedOptions: {},
};

const CommonSlice = createSlice({
  name: 'common',
  initialState: initialState,
  reducers: {
    SetSnackBar(
      state,
      action: PayloadAction<{
        open?: boolean;
        message: string;
        variant?: 'info' | 'success' | 'error' | 'warning';
        duration?: number;
      }>,
    ) {
      state.snackbar = { open: true, variant: 'error', duration: 2000, ...action.payload };
    },
    SetLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload;
    },
    PostOrganisationLoading(state, action: PayloadAction<boolean>) {
      state.postOrganisationLoading = action.payload;
    },
    SetProjectNotFound(state, action: PayloadAction<boolean>) {
      state.projectNotFound = action.payload;
    },
    // set previous selected options of select component
    SetPreviousSelectedOptions(state, action: PayloadAction<{ key: string; options: selectOptionsType[] }>) {
      state.previousSelectedOptions[action.payload.key] = action.payload.options;
    },
  },
});

export const CommonActions = CommonSlice.actions;
export default CommonSlice;
