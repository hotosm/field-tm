import { combineReducers, configureStore } from "@reduxjs/toolkit";
import homeSlice from 'fmtm/HomeSlice';
import themeSlice from 'fmtm/ThemeSlice';
import MapTasksSlice from "./slices/MapTasksSlice";
import ProjectSlice from "./slices/ProjectSlice";
import storage from 'redux-persist/lib/storage';
import { persistReducer, persistStore } from 'redux-persist';
import thunk from "redux-thunk";

const persistConfig = {
    key: 'root',
    storage,
}

const reducers = combineReducers({
    project: ProjectSlice.reducer,
    theme: themeSlice.reducer,
    home: homeSlice.reducer,
    maptasks: MapTasksSlice.reducer
});

const persistedReducer = persistReducer(persistConfig, reducers)
export const store = configureStore({
    reducer: persistedReducer,
    middleware: [thunk]
})

export const persistor = persistStore(store)