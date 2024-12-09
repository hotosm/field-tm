import { createSlice } from '@reduxjs/toolkit';
import { HomeStateTypes } from '@/store/types/IHome';

export const initialState: HomeStateTypes = {
  homeProjectSummary: [],
  homeProjectLoading: true,
  selectedProject: {},
  dialogStatus: false,
  snackbar: {
    open: false,
    message: '',
    variant: 'info',
    duration: 0,
  },
  showMapStatus: false,
  projectCentroidLoading: false,
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
    SetHomeProjectSummary(state, action) {
      state.homeProjectSummary = action.payload;
    },
    HomeProjectLoading(state, action) {
      state.homeProjectLoading = action.payload;
    },
    SetSelectedProject(state, action) {
      state.selectedProject = action.payload;
    },
    SetDialogStatus(state, action) {
      state.dialogStatus = action.payload;
    },
    SetSnackBar(state, action) {
      state.snackbar = action.payload;
    },
    SetShowMapStatus(state, action) {
      state.showMapStatus = action.payload;
    },
    SetProjectCentroidLoading(state, action) {
      state.projectCentroidLoading = action.payload;
    },
    SetProjectCentroid(state, action) {
      state.homeProjectSummary = action.payload;
    },
    SetHomeProjectPagination(state, action) {
      state.homeProjectPagination = action.payload;
    },
  },
});

export const HomeActions = HomeSlice.actions;
export default HomeSlice;
