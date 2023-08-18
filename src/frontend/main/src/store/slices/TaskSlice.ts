import { createSlice } from '@reduxjs/toolkit';

const TaskSlice = createSlice({
  name: 'task',
  initialState: {
    taskLoading: false,
    taskInfo: [],
    selectedTask: null,
    projectBoundaryLoading: false,
    projectBoundary: [],
    convertToOsmLoading: null,
    convertToOsm: [],
    downloadSubmissionLoading: { type: '', loading: false },
    convertXMLToJOSMLoading: false,
    josmEditorError: null,
  },
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
      state.taskInfo = action.payload;
    },
    SetSelectedTask(state, action) {
      state.selectedTask = action.payload;
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
