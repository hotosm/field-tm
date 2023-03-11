import { createSlice } from "@reduxjs/toolkit";


const ProjectSlice = createSlice({
    name: 'project',
    initialState: {
        projectLoading: true,
        projectTaskBoundries: [],
        newProjectTrigger: false,
        projectInfo: {},

    },
    reducers: {
        SetProjectTaskBoundries(state, action) {
            state.projectTaskBoundries = action.payload
        },
        SetProjectLoading(state, action) {
            state.projectLoading = action.payload
        },
        SetProjectInfo(state, action) {
            state.projectInfo = action.payload
        },
        SetNewProjectTrigger(state, action) {
            state.newProjectTrigger = !state.newProjectTrigger
        }
    }
})


export const ProjectActions = ProjectSlice.actions;
export default ProjectSlice;