import { taskSubmissionInfoType } from '@/models/task/taskModel';

export type TaskStateTypes = {
  taskLoading: boolean;
  taskInfo: taskSubmissionInfoType[];
  selectedTask: number | null;
  selectedFeatureProps: number | null;
  projectBoundaryLoading: boolean;
  projectBoundary: [];
  convertToOsmLoading: boolean;
  convertToOsm: [];
  downloadSubmissionLoading: downloadSubmissionLoadingTypes;
  convertXMLToJOSMLoading: boolean;
  josmEditorError: null | string;
};

type downloadSubmissionLoadingTypes = {
  type: '' | 'json' | 'csv';
  loading: boolean;
};
