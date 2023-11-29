import { createSlice } from '@reduxjs/toolkit';
import storage from 'redux-persist/lib/storage';

const ProjectSlice = createSlice({
  name: 'project',
  initialState: {
    projectLoading: true,
    projectTaskBoundries: [],
    newProjectTrigger: false,
    projectInfo: {},
    projectSubmissionLoading: false,
    projectSubmission: [],
    projectBuildingGeojsonLoading: false,
    projectBuildingGeojson: [],
    downloadProjectFormLoading: { type: 'form', loading: false },
    generateProjectTilesLoading: false,
    tilesList: [],
    tilesListLoading: false,
    downloadTilesLoading: false,
    downloadDataExtractLoading: false,
    taskModalStatus: false,
    mobileFooterSelection: 'explore',
    geolocationStatus: false,
  },
  reducers: {
    SetProjectTaskBoundries(state, action) {
      state.projectTaskBoundries = action.payload;
    },
    SetProjectLoading(state, action) {
      state.projectLoading = action.payload;
    },
    SetProjectInfo(state, action) {
      state.projectInfo = action.payload;
    },
    SetNewProjectTrigger(state, action) {
      state.newProjectTrigger = !state.newProjectTrigger;
    },
    clearProjects(state, action) {
      storage.removeItem('persist:project');
      state.projectTaskBoundries = action.payload;
    },
    GetProjectSubmissionLoading(state, action) {
      state.projectSubmissionLoading = action.payload;
    },
    SetProjectSubmission(state, action) {
      state.projectSubmission = action.payload;
    },
    GetProjectBuildingGeojsonLoading(state, action) {
      state.projectSubmissionLoading = action.payload;
    },
    SetProjectBuildingGeojson(state, action) {
      state.projectBuildingGeojson = action.payload;
    },
    SetDownloadProjectFormLoading(state, action) {
      state.downloadProjectFormLoading = action.payload;
    },
    SetGenerateProjectTilesLoading(state, action) {
      state.generateProjectTilesLoading = action.payload;
    },
    SetTilesList(state, action) {
      state.tilesList = action.payload;
    },
    SetTilesListLoading(state, action) {
      state.tilesListLoading = action.payload;
    },
    SetDownloadTileLoading(state, action) {
      state.downloadTilesLoading = action.payload;
    },
    SetDownloadDataExtractLoading(state, action) {
      state.downloadDataExtractLoading = action.payload;
    },
    ToggleTaskModalStatus(state, action) {
      state.taskModalStatus = action.payload;
    },
    SetMobileFooterSelection(state, action) {
      state.mobileFooterSelection = action.payload;
    },
    ToggleGeolocationStatus(state, action) {
      state.geolocationStatus = action.payload;
    },
  },
});

export const ProjectActions = ProjectSlice.actions;
export default ProjectSlice;
