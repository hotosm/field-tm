import {
  downloadProjectFormLoadingType,
  projectDashboardDetailTypes,
  projectInfoType,
  projectTaskBoundriesType,
} from '@/models/project/projectModel';

export type ProjectStateTypes = {
  projectLoading: boolean;
  projectTaskBoundries: projectTaskBoundriesType[];
  newProjectTrigger: boolean;
  projectInfo: Partial<projectInfoType>;
  projectSubmissionLoading: boolean;
  projectSubmission: [];
  projectDataExtractLoading: boolean;
  downloadProjectFormLoading: downloadProjectFormLoadingType;
  generateProjectTilesLoading: boolean;
  tilesList: tilesListTypes[];
  tilesListLoading: boolean;
  downloadTilesLoading: boolean;
  downloadDataExtractLoading: boolean;
  taskModalStatus: boolean;
  toggleGenerateMbTilesModal: boolean;
  mobileFooterSelection: string;
  projectDetailsLoading: boolean;
  projectDashboardDetail: projectDashboardDetailTypes;
  entityOsmMap: EntityOsmMap[];
  entityOsmMapLoading: boolean;
  projectDashboardLoading: boolean;
  geolocationStatus: boolean;
  projectCommentsList: projectCommentsListTypes[];
  projectPostCommentsLoading: boolean;
  projectGetCommentsLoading: boolean;
  clearEditorContent: boolean;
  projectOpfsBasemapPath: string | null;
  projectTaskActivity: projectTaskActivity[];
  projectActivityLoading: boolean;
};

export type EntityOsmMap = {
  id: string;
  osm_id: string;
  status: number;
  task_id: number;
  updated_at: string;
};

type tilesListTypes = {
  id: number;
  project_id: number;
  status: string;
  tile_source: string;
};

type projectCommentsListTypes = {
  id: number;
  project_id: number;
  action: string;
  action_text: string;
  action_date: string;
  username: string;
  task_id: number;
  profile_img: string;
  status: any;
};

type projectTaskActivity = {
  id: number;
  project_id: number;
  task_id: number;
  action: string;
  action_text: string;
  action_date: string;
  status: string;
  profile_img: null | string;
  username: string;
};
