import HomeSlice from "./slices/HomeSlice";
import ThemeSlice from "./slices/ThemeSlice";
import projectSlice from 'map/Project';
import CoreModules from '../shared/CoreModules';
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

const reducers = CoreModules.combineReducers({
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

export const store = CoreModules.configureStore({
    reducer: reducers,
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            serializableCheck: {
                ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
            },
        }),
})

export const persistor = persistStore(store)
