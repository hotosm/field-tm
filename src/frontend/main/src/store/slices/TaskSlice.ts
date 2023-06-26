import { createSlice } from "@reduxjs/toolkit";

const TaskSlice = createSlice({
    name: 'task',
    initialState: {
        taskLoading: true,
        taskInfo: [],
        selectedTask: null,
        projectSubmissionLoading: true,
        projectSubmission: [],
        convertToOsmLoading: null,
        convertToOsm: [],
    },
    reducers: {
        SetTaskLoading(state, action) {
            state.taskLoading = action.payload
        },
        GetProjectSubmissionLoading(state, action) {
            state.projectSubmissionLoading = action.payload
        },
        FetchConvertToOsmLoading(state, action) {
            state.convertToOsmLoading = action.payload
        },
        FetchTaskInfoDetails(state, action) {
            state.taskInfo = action.payload;
        },
        SetSelectedTask(state, action) {
            state.selectedTask = action.payload;
        },
 
        GetDownloadProjectSubmission(state, action) {
            state.projectSubmission = action.payload;
        },
        FetchConvertToOsm(state, action) {
            state.convertToOsm = action.payload;
        }
    },
})

export const TaskActions = TaskSlice.actions;
export default TaskSlice;