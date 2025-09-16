import {
  downloadProjectFormLoadingType,
  EntityOsmMap,
  projectInfoType,
  projectTaskBoundriesType,
  tileType,
} from '@/models/project/projectModel';
import { project_status, user_roles } from '@/types/enums';

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
  mobileFooterSelection: '' | 'projectInfo' | 'activities' | 'comment' | 'instructions' | 'infographics';
  projectDetailsLoading: boolean;
  entityOsmMap: EntityOsmMap[];
  entityOsmMapLoading: boolean;
  updateEntityStateLoading: boolean;
  projectCommentsList: projectCommentsListTypes[];
  projectPostCommentsLoading: boolean;
  projectGetCommentsLoading: boolean;
  clearEditorContent: boolean;
  projectTaskActivity: projectTaskActivity[];
  projectActivityLoading: boolean;
  downloadSubmissionLoading: boolean;
  syncTaskStateLoading: boolean;
  selectedEntityId: string | null;
  badGeomFeatureCollection: FeatureCollectionType;
  newGeomFeatureCollection: FeatureCollectionType;
  OdkEntitiesGeojsonLoading: boolean;
  isEntityDeleting: Record<string, boolean>;
  projectUsers: { user_sub: string; project_id: number; role: user_roles; username: string }[];
  projectUsersLoading: boolean;
  unassigningUserFromProject: boolean;
  projectTaskIdIndexMap: Record<number, number>;
};

type projectCommentsListTypes = {
  event_id: number;
  task_id: number;
  event: string;
  username: string;
  comment: string;
  created_at: string;
  profile_img: string;
  state: any;
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

export type FeatureCollectionType = {
  type: 'FeatureCollection';
  features: featureType[];
};

export type featureType = {
  id?: string;
  type: 'Feature';
  geometry: { type: string; coordinates: number[][][] };
  properties: Record<string, any>;
};

export type projectStatusOptionsType = {
  name: string;
  value: project_status;
  label: string;
};
