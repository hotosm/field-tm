import { createSlice } from "@reduxjs/toolkit";


const ProjectSlice = createSlice({
    name: 'project',
    initialState: {
        projectLoading: true,
        projectData:{},
        dialogStatus:false
    },
    reducers: {
        SetProject(state, action) {
            state.projectData = action.payload
        },
        SetProjectLoading(state, action) {
            state.projectLoading = action.payload
        },
        SetDialogStatus(state,action){
            state.dialogStatus = action.payload
        }

    }
})


export const ProjectActions = ProjectSlice.actions;
export default ProjectSlice;