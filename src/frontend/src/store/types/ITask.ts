import { taskDataTypes } from '@/models/submission/submissionModel';
import { taskInfoType } from '@/models/task/taskModel';

export type TaskStateTypes = {
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

type downloadSubmissionLoadingTypes = {
  type: '' | 'json' | 'csv';
  loading: boolean;
};
