import { createSlice } from "@reduxjs/toolkit";


const ProjectSlice = createSlice({
    name: 'project',
    initialState: {
        projectLoading: true,
        projectData:{},
        dialogStatus:false,
        map:null
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
        },
        SetMap(state,action){
            state.map = action.payload
        }
    }
})


export const ProjectActions = ProjectSlice.actions;
export default ProjectSlice;