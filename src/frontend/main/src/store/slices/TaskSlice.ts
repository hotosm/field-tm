import { createSlice } from "@reduxjs/toolkit";

const  TaskSlice = createSlice({
    name : 'task',
    initialState: {
        taskLoading: true,
        taskInfo: {},
    },
    reducers: {
        SetTaskLoading(state, action) {
            state.taskLoading = action.payload
        },
        FetchTaskInfoDetails(state, action) {
             state.taskInfo = action.payload;
        }
    },
})

    export const TaskActions = TaskSlice.actions;
    export default TaskSlice;