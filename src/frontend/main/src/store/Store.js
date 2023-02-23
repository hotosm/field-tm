import { combineReducers } from 'redux'
import { configureStore } from '@reduxjs/toolkit';
import HomeSlice from "./slices/HomeSlice";
import ThemeSlice from "./slices/ThemeSlice";
import projectSlice from 'map/Project';

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
import storage from 'redux-persist/lib/storage';

const reducers = combineReducers({
    project: persistReducer(
        {
            key: 'project',
            storage
        },
        projectSlice.reducer
    ),
    //you can persist your auth reducer here similar to project reducer
    home: HomeSlice.reducer,
    theme: ThemeSlice.reducer,
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
