import { createSlice } from "@reduxjs/toolkit";

const TaskSlice = createSlice({
    name: 'task',
    initialState: {
        taskLoading: true,
        taskInfo: [],
        selectedTask: null,
        projectBoundaryLoading: true,
        projectBoundary: [],
        convertToOsmLoading: null,
        convertToOsm: [],
    },
    reducers: {
        SetTaskLoading(state, action) {
            state.taskLoading = action.payload
        },
        GetProjectBoundaryLoading(state, action) {
            state.projectBoundaryLoading = action.payload
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
 
        GetDownloadProjectBoundary(state, action) {
            state.projectBoundary = action.payload;
        },
        FetchConvertToOsm(state, action) {
            state.convertToOsm = action.payload;
        }
    },
})

export const TaskActions = TaskSlice.actions;
export default TaskSlice;