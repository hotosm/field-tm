import { combineReducers, configureStore } from "@reduxjs/toolkit";
import themeSlice from 'fmtm/ThemeSlice';
import homeSlice from 'fmtm/HomeSlice';
import ProjectSlice from "./slices/ProjectSlice";
import {
    persistStore,
    persistReducer,
    FLUSH,
    REHYDRATE,
    PAUSE,
    PERSIST,
    PURGE,
    REGISTER,
} from 'redux-persist'
import storage from 'redux-persist/lib/storage'

const reducers = combineReducers({
    project: persistReducer(
        {
            key: 'project',
            storage
        },
        ProjectSlice.reducer
    ),
    theme: themeSlice.reducer,
    home: homeSlice.reducer
})

export const store = configureStore({
    reducer: reducers,
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            serializableCheck: {
                ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
            },
        }),
})


export const persistor = persistStore(store)
