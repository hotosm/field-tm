import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { HomeStateTypes } from '@/store/types/IHome';

export const initialState: HomeStateTypes = {
  homeProjectSummary: [],
  homeProjectLoading: true,
  selectedProject: {},
  snackbar: {
    open: false,
    message: '',
    variant: 'info',
    duration: 0,
  },
  showMapStatus: false,
  homeProjectPagination: {
    has_next: false,
    has_prev: false,
    next_num: null,
    page: null,
    pages: null,
    prev_num: null,
    per_page: null,
    total: null,
  },
};

const HomeSlice = createSlice({
  name: 'home',
  initialState: initialState,
  reducers: {
    SetHomeProjectSummary(state, action: PayloadAction<HomeStateTypes['homeProjectSummary']>) {
      state.homeProjectSummary = action.payload;
    },
    HomeProjectLoading(state, action: PayloadAction<boolean>) {
      state.homeProjectLoading = action.payload;
    },
    SetSelectedProject(state, action: PayloadAction<HomeStateTypes['selectedProject']>) {
      state.selectedProject = action.payload;
    },
    SetSnackBar(state, action: PayloadAction<HomeStateTypes['snackbar']>) {
      state.snackbar = action.payload;
    },
    SetShowMapStatus(state, action: PayloadAction<boolean>) {
      state.showMapStatus = action.payload;
    },
    SetHomeProjectPagination(state, action: PayloadAction<HomeStateTypes['homeProjectPagination']>) {
      state.homeProjectPagination = action.payload;
    },
  },
});

export const HomeActions = HomeSlice.actions;
export default HomeSlice;
