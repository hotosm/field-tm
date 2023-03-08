import { createSlice } from "@reduxjs/toolkit";
import React from "react";

const HomeSlice = createSlice({
    name: 'home',
    initialState: {
        homeProjectSummary: [],
        homeProjectLoading: true,
        selectedProject: {},

    },
    reducers: {
        SetHomeProjectSummary(state, action) {
            state.homeProjectSummary = action.payload
        },
        HomeProjectLoading(state, action) {
            state.homeProjectLoading = action.payload
        },
        SetSelectedProject(state, action) {
            state.selectedProject = action.payload
        },
    }
})


export const HomeActions = HomeSlice.actions;
export default HomeSlice;
