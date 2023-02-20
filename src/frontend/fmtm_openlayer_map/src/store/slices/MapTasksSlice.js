import { createSlice } from "@reduxjs/toolkit";

const MapTasksSlice = createSlice({
    name:'maptasks',
    initialState:{
        features:{},
        map:{},
    },
    reducers:{
        SetMap(state,actions){
            state.map = actions.payload
        },
        SetFeature(state,actions){
            state.features = actions.payload
        },
    }
})

export const MapTasksActions = MapTasksSlice.actions;
export default MapTasksSlice;