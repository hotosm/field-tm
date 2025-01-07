import {
  downloadProjectFormLoadingType,
  EntityOsmMap,
  projectDashboardDetailTypes,
  projectInfoType,
  projectTaskBoundriesType,
  tileType,
} from '@/models/project/projectModel';

export type ProjectStateTypes = {
  projectTaskBoundries: projectTaskBoundriesType[];
  newProjectTrigger: boolean;
  projectInfo: Partial<projectInfoType>;
  projectDataExtractLoading: boolean;
  downloadProjectFormLoading: downloadProjectFormLoadingType;
  generateProjectTilesLoading: boolean;
  tilesList: tileType[];
  tilesListLoading: boolean;
  customBasemapUrl: string | null;
  downloadDataExtractLoading: boolean;
  taskModalStatus: boolean;
  toggleGenerateMbTilesModal: boolean;
  mobileFooterSelection: string;
  projectDetailsLoading: boolean;
  projectDashboardDetail: projectDashboardDetailTypes | null;
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
