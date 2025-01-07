import { taskSubmissionInfoType } from '@/models/task/taskModel';

export type TaskStateTypes = {
  taskLoading: boolean;
  taskInfo: taskSubmissionInfoType[];
  selectedTask: number | null;
  selectedFeatureProps: TaskFeatureSelectionProperties;
  projectBoundaryLoading: boolean;
  convertToOsmLoading: boolean;
  downloadSubmissionLoading: downloadSubmissionLoadingTypes;
  convertXMLToJOSMLoading: boolean;
  josmEditorError: null | string;
};

type downloadSubmissionLoadingTypes = {
  type: '' | 'json' | 'csv';
  loading: boolean;
};

export type TaskFeatureSelectionProperties = {
  osm_id: number;
  tags: string;
  timestamp: string;
  version: number;
  changeset: number;
};
