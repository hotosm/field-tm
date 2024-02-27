import { downloadProjectFormLoadingType, projectInfoType, taskHistoryTypes } from '@/models/project/projectModel';

export type ProjectStateTypes = {
  projectLoading: boolean;
  projectTaskBoundries: projectTaskBoundriesType[];
  newProjectTrigger: boolean;
  projectInfo: projectInfoType | {};
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
  mobileFooterSelection: string;
  geolocationStatus: boolean;
  projectDetailsLoading: boolean;
  projectDashboardDetail: projectDashboardDetailTypes;
  projectDashboardLoading: boolean;
};

type projectTaskBoundriesType = {
  id: number;
  taskBoundries: taskBoundriesTypes[];
};

type taskBoundriesTypes = {
  bbox: [number, number];
  id: number;
  locked_by_uid: null | string;
  locked_by_username: null | string;
  odk_token: string;
  outline_geojson: {
    type: string;
    geometry: {
      coordinates: [string, string];
      type: string;
    };
    properties: Record<string, any>;
    id: string;
    bbox: [string, string, string, string];
  };
  outline_centroid: {
    type: string;
    geometry: {
      coordinates: [string, string];
      type: string;
    };
    properties: Record<string, any>;
    id: string;
    bbox: [string, string, string, string];
  };
  task_history: taskHistoryTypes[];
  task_status: string;
};

type tilesListTypes = {
  id: number;
  project_id: number;
  status: string;
  tile_source: string;
};

type projectDashboardDetailTypes = {
  project_name_prefix: string;
  organisation_name: string;
  total_tasks: number | null;
  created: string;
  organisation_logo: string;
  total_submission: number | null;
  total_contributors: number | null;
  last_active: string;
};
