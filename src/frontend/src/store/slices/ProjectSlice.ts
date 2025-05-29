import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import storage from 'redux-persist/lib/storage';
import { featureType, ProjectStateTypes } from '@/store/types/IProject';

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
  projectCommentsList: [],
  projectPostCommentsLoading: false,
  projectGetCommentsLoading: false,
  clearEditorContent: false,
  projectTaskActivity: [],
  projectActivityLoading: false,
  downloadSubmissionLoading: false,
  syncTaskStateLoading: false,
  selectedEntityId: null,
  badGeomFeatureCollection: { type: 'FeatureCollection', features: [] },
  newGeomFeatureCollection: { type: 'FeatureCollection', features: [] },
  OdkEntitiesGeojsonLoading: false,
  isEntityDeleting: {},
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
    SyncTaskStateLoading(state, action: PayloadAction<boolean>) {
      state.syncTaskStateLoading = action.payload;
    },
    SetSelectedEntityId(state, action: PayloadAction<string | null>) {
      state.selectedEntityId = action.payload;
    },
    SetOdkEntitiesGeojson(state, action: PayloadAction<{ type: 'FeatureCollection'; features: featureType[] }>) {
      const features = action.payload.features;
      const newFeatures = features?.filter((feature) => !!feature.properties?.created_by);
      const badFeatures = features?.filter((feature) => feature.properties?.status === '6');

      state.newGeomFeatureCollection = { type: 'FeatureCollection', features: newFeatures };
      state.badGeomFeatureCollection = { type: 'FeatureCollection', features: badFeatures };
    },
    SetOdkEntitiesGeojsonLoading(state, action: PayloadAction<boolean>) {
      state.OdkEntitiesGeojsonLoading = action.payload;
    },
    SetIsEntityDeleting(state, action: PayloadAction<Record<string, boolean>>) {
      state.isEntityDeleting = { ...state.isEntityDeleting, ...action.payload };
    },
    RemoveNewEntity(state, action) {
      state.newGeomFeatureCollection = {
        ...state.newGeomFeatureCollection,
        features: state.newGeomFeatureCollection.features.filter((feature) => feature?.id !== action.payload),
      };
    },
  },
});

export const ProjectActions = ProjectSlice.actions;
export default ProjectSlice;
