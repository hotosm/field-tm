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
  customBasemapUrl: string | null;
  downloadDataExtractLoading: boolean;
  taskModalStatus: boolean;
  toggleGenerateMbTilesModal: boolean;
  mobileFooterSelection: string;
  projectDetailsLoading: boolean;
  projectDashboardDetail: projectDashboardDetailTypes;
  entityOsmMap: EntityOsmMap[];
  entityOsmMapLoading: boolean;
  updateEntityStateLoading: boolean;
  projectDashboardLoading: boolean;
  geolocationStatus: boolean;
  projectCommentsList: projectCommentsListTypes[];
  projectPostCommentsLoading: boolean;
  projectGetCommentsLoading: boolean;
  clearEditorContent: boolean;
  projectTaskActivity: projectTaskActivity[];
  projectActivityLoading: boolean;
  downloadSubmissionLoading: boolean;
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
  source: string;
  format: string;
  url: string;
};

type projectCommentsListTypes = {
  id: number;
  task_id: number;
  comment: string;
  created_at: string;
  username: string;
  profile_img: string;
};

export type projectTaskActivity = {
  event_id: string;
  task_id: number;
  event: string;
  state: string;
  comment: string;
  profile_img: null | string;
  username: string;
  created_at: string;
};
