import CoreModules from '../../shared/CoreModules';
const HomeSlice = CoreModules.createSlice({
  name: 'home',
  initialState: {
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
    showMapStatus: true,
    projectCentroidLoading: false,
  },
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
  },
});

export const HomeActions = HomeSlice.actions;
export default HomeSlice;
