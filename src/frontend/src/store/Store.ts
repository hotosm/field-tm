import React from "react";
import { configureStore } from '@reduxjs/toolkit';
import HomeSlice from "../slices/HomeSlice";
const store = configureStore({
    reducer: {
        home: HomeSlice.reducer
    }
})
export default store;

