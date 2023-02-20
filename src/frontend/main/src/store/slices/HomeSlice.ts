import { createSlice } from "@reduxjs/toolkit";
import React from "react";

const HomeSlice = createSlice({
    name: 'home',
    initialState: {
        homeProjectSummary: [],
        homeProjectLoading: true,
        projectId: null,
    },
    reducers: {
        SetHomeProjectSummary(state, action) {
            state.homeProjectSummary = action.payload
        },
        HomeProjectLoading(state, action) {
            state.homeProjectLoading = action.payload
        },
        SetProjectId(state, action) {
            state.projectId = action.payload
        }
    }
})


export const HomeActions = HomeSlice.actions;
export default HomeSlice;