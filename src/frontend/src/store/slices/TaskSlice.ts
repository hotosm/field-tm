import { createSlice } from '@reduxjs/toolkit';
import { TaskStateTypes } from '@/store/types/ITask';
import { taskInfoType } from '@/models/task/taskModel';

const initialState: TaskStateTypes = {
  taskLoading: false,
  taskInfo: [],
  selectedTask: null,
  selectedFeatureProps: null,
  projectBoundaryLoading: false,
  projectBoundary: [],
  convertToOsmLoading: false,
  convertToOsm: [],
  downloadSubmissionLoading: { type: '', loading: false },
  convertXMLToJOSMLoading: false,
  josmEditorError: null,
  taskData: { feature_count: 0, submission_count: 0, task_count: 0 },
};

const TaskSlice = createSlice({
  name: 'task',
  initialState: initialState,
  reducers: {
    SetTaskLoading(state, action) {
      state.taskLoading = action.payload;
    },
    GetProjectBoundaryLoading(state, action) {
      state.projectBoundaryLoading = action.payload;
    },
    FetchConvertToOsmLoading(state, action) {
      state.convertToOsmLoading = action.payload;
    },
    FetchTaskInfoDetails(state, action) {
      const taskInfo: taskInfoType[] = action.payload;

      state.taskInfo = taskInfo;

      const featureSubmissionCount = taskInfo.reduce(
        (accumulator, current) => {
          accumulator.feature_count += current.feature_count;
          accumulator.submission_count += current.submission_count;
          return accumulator;
        },
        { feature_count: 0, submission_count: 0 },
      );
      const tasks = taskInfo.length;
      state.taskData = { ...featureSubmissionCount, task_count: tasks };
    },

    SetSelectedTask(state, action) {
      state.selectedTask = action.payload;
    },

    SetSelectedFeatureProps(state, action) {
      state.selectedFeatureProps = action.payload;
    },

    GetDownloadProjectBoundary(state, action) {
      state.projectBoundary = action.payload;
    },
    FetchConvertToOsm(state, action) {
      state.convertToOsm = action.payload;
    },
    GetDownloadProjectSubmissionLoading(state, action) {
      state.downloadSubmissionLoading = action.payload;
    },
    SetConvertXMLToJOSMLoading(state, action) {
      state.convertXMLToJOSMLoading = action.payload;
    },
    SetJosmEditorError(state, action) {
      state.josmEditorError = action.payload;
    },
  },
});

export const TaskActions = TaskSlice.actions;
export default TaskSlice;
