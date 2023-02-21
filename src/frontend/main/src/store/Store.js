import React from "react";
import { configureStore } from '@reduxjs/toolkit';
import HomeSlice from "./slices/HomeSlice";
import ThemeSlice from "./slices/ThemeSlice";
import projectSlice from 'map/Project'
const store = configureStore({
    reducer: {
        home: HomeSlice.reducer,
        theme: ThemeSlice.reducer,
        project: projectSlice.reducer
    }
})
export default store;

