import React from "react";
import { configureStore } from '@reduxjs/toolkit';
import HomeSlice from "./slices/HomeSlice";
import ThemeSlice from "./slices/ThemeSlice";
const store = configureStore({
    reducer: {
        home: HomeSlice.reducer,
        theme: ThemeSlice.reducer
    }
})
export default store;

