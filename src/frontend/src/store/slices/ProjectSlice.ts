import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import storage from 'redux-persist/lib/storage';
import { ProjectStateTypes } from '@/store/types/IProject';
import { geometryLogResponseType } from '@/models/project/projectModel';

const initialState: ProjectStateTypes = {
  projectTaskBoundries: [],
  newProjectTrigger: false,
  projectInfo: {},
  projectDataExtractLoading: false,
  downloadProjectFormLoading: { type: 'form', loading: false },
  generateProjectTilesLoading: false,
  tilesList: [],
  tilesListLoading: false,
  customBasemapUrl: null,
  downloadDataExtractLoading: false,
  taskModalStatus: false,
  toggleGenerateMbTilesModal: false,
  mobileFooterSelection: 'explore',
  projectDetailsLoading: true,
  projectDashboardDetail: null,
  entityOsmMap: [],
  entityOsmMapLoading: false,
  updateEntityStateLoading: false,
  projectDashboardLoading: false,
  geolocationStatus: false,
  projectCommentsList: [],
  projectPostCommentsLoading: false,
  projectGetCommentsLoading: false,
  clearEditorContent: false,
  projectTaskActivity: [],
  projectActivityLoading: false,
  downloadSubmissionLoading: false,
  badGeomFeatureCollection: { type: 'FeatureCollection', features: [] },
  newGeomFeatureCollection: { type: 'FeatureCollection', features: [] },
  badGeomLogList: [],
  getGeomLogLoading: false,
  syncTaskStateLoading: false,
};

const ProjectSlice = createSlice({
  name: 'project',
  initialState: initialState,
  reducers: {
    SetProjectTaskBoundries(state, action: PayloadAction<ProjectStateTypes['projectTaskBoundries']>) {
      state.projectTaskBoundries = action.payload;
    },
    SetProjectInfo(state, action) {
      state.projectInfo = action.payload;
    },
    SetNewProjectTrigger(state) {
      state.newProjectTrigger = !state.newProjectTrigger;
    },
    clearProjects(state, action: PayloadAction<[]>) {
      storage.removeItem('persist:project');
      state.projectTaskBoundries = action.payload;
    },
    SetDownloadProjectFormLoading(state, action: PayloadAction<ProjectStateTypes['downloadProjectFormLoading']>) {
      state.downloadProjectFormLoading = action.payload;
    },
    SetGenerateProjectTilesLoading(state, action: PayloadAction<boolean>) {
      state.generateProjectTilesLoading = action.payload;
    },
    SetTilesList(state, action: PayloadAction<ProjectStateTypes['tilesList']>) {
      state.tilesList = action.payload;
    },
    SetTilesListLoading(state, action: PayloadAction<boolean>) {
      state.tilesListLoading = action.payload;
    },
    SetPmtileBasemapUrl(state, action: PayloadAction<string | null>) {
      state.customBasemapUrl = action.payload;
    },
    SetDownloadDataExtractLoading(state, action: PayloadAction<boolean>) {
      state.downloadDataExtractLoading = action.payload;
    },
    ToggleTaskModalStatus(state, action: PayloadAction<boolean>) {
      state.taskModalStatus = action.payload;
    },
    ToggleGenerateMbTilesModalStatus(state, action: PayloadAction<boolean>) {
      state.toggleGenerateMbTilesModal = action.payload;
    },
    SetMobileFooterSelection(state, action: PayloadAction<string>) {
      state.mobileFooterSelection = action.payload;
    },
    SetProjectDetialsLoading(state, action: PayloadAction<boolean>) {
      state.projectDetailsLoading = action.payload;
    },
    SetProjectDashboardDetail(state, action: PayloadAction<ProjectStateTypes['projectDashboardDetail']>) {
      state.projectDashboardDetail = action.payload;
    },
    SetEntityToOsmIdMapping(state, action: PayloadAction<ProjectStateTypes['entityOsmMap']>) {
      state.entityOsmMap = action.payload;
    },
    SetEntityToOsmIdMappingLoading(state, action: PayloadAction<boolean>) {
      state.entityOsmMapLoading = action.payload;
    },
    SetProjectDashboardLoading(state, action: PayloadAction<boolean>) {
      state.projectDashboardLoading = action.payload;
    },
    ToggleGeolocationStatus(state, action: PayloadAction<boolean>) {
      state.geolocationStatus = action.payload;
    },
    SetProjectCommentsList(state, action) {
      state.projectCommentsList = action.payload;
    },
    SetPostProjectCommentsLoading(state, action: PayloadAction<boolean>) {
      state.projectPostCommentsLoading = action.payload;
    },
    SetProjectGetCommentsLoading(state, action: PayloadAction<boolean>) {
      state.projectGetCommentsLoading = action.payload;
    },
    ClearEditorContent(state, action: PayloadAction<boolean>) {
      state.clearEditorContent = action.payload;
    },
    UpdateProjectCommentsList(state, action) {
      state.projectCommentsList = [...state.projectCommentsList, action.payload];
    },
    SetProjectTaskActivity(state, action) {
      state.projectTaskActivity = action.payload;
    },
    SetProjectTaskActivityLoading(state, action: PayloadAction<boolean>) {
      state.projectActivityLoading = action.payload;
    },
    UpdateProjectTaskActivity(state, action) {
      state.projectTaskActivity = [action.payload, ...state.projectTaskActivity];
    },
    UpdateEntityStateLoading(state, action: PayloadAction<boolean>) {
      state.updateEntityStateLoading = action.payload;
    },
    UpdateEntityState(state, action) {
      const updatedEntityOsmMap = state.entityOsmMap?.map((entity) => {
        if (entity.id === action.payload.id) {
          return action.payload;
        }
        return entity;
      });
      state.entityOsmMap = updatedEntityOsmMap;
    },
    UpdateProjectTaskBoundries(state, action) {
      const updatedProjectTaskBoundries = state.projectTaskBoundries?.map((boundary) => {
        if (boundary.id == action.payload.projectId) {
          const updatedBoundary = boundary?.taskBoundries?.map((taskBoundary) => {
            if (taskBoundary?.id === +action.payload.taskId) {
              return {
                ...taskBoundary,
                task_state: action.payload.task_state,
                actioned_by_uid: action.payload.actioned_by_uid,
                actioned_by_username: action.payload.actioned_by_username,
              };
            }
            return taskBoundary;
          });
          return { id: boundary.id, taskBoundries: updatedBoundary };
        }
        return boundary;
      });
      state.projectTaskBoundries = updatedProjectTaskBoundries;
    },
    SetDownloadSubmissionGeojsonLoading(state, action: PayloadAction<boolean>) {
      state.downloadSubmissionLoading = action.payload;
    },
    SetGeometryLog(state, action: PayloadAction<geometryLogResponseType[]>) {
      const geomLog = action.payload;
      const badGeomLog = geomLog.filter((geom) => geom.status === 'BAD');
      const badGeomLogGeojson = badGeomLog.map((geom) => geom.geojson);
      const newGeomLogGeojson = geomLog.filter((geom) => geom.status === 'NEW').map((geom) => geom.geojson);
      state.badGeomFeatureCollection = { type: 'FeatureCollection', features: badGeomLogGeojson };
      state.newGeomFeatureCollection = { type: 'FeatureCollection', features: newGeomLogGeojson };
      state.badGeomLogList = badGeomLog;
    },
    SetGeometryLogLoading(state, action: PayloadAction<boolean>) {
      state.getGeomLogLoading = action.payload;
    },
    SyncTaskStateLoading(state, action: PayloadAction<boolean>) {
      state.syncTaskStateLoading = action.payload;
    },
  },
});

export const ProjectActions = ProjectSlice.actions;
export default ProjectSlice;
