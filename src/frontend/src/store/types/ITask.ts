export type ITaskSlice = {
  taskLoading: boolean;
  taskInfo: taskInfoType[];
  selectedTask: number | null;
  projectBoundaryLoading: boolean;
  projectBoundary: [];
  convertToOsmLoading: boolean;
  convertToOsm: [];
  downloadSubmissionLoading: downloadSubmissionLoadingTypes;
  convertXMLToJOSMLoading: boolean;
  josmEditorError: null | string;
  taskData: taskDataTypes;
};

export type taskInfoType = {
  task_id: string;
  submission_count: number;
  last_submission: string | null;
  feature_count: number;
};

type downloadSubmissionLoadingTypes = {
  type: '' | 'json' | 'csv';
  loading: boolean;
};

type taskDataTypes = {
  feature_count: number;
  submission_count: number;
  task_count: number;
};
