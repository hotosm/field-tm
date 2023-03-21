import HomeSlice from "./slices/HomeSlice";
import ThemeSlice from "./slices/ThemeSlice";
// import projectSlice from 'map/Project';
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
import ProjectSlice from "./slices/ProjectSlice";
import CreateProjectSlice from "./slices/CreateProjectSlice";

const reducers = CoreModules.combineReducers({
    project: persistReducer(
        {
            key: 'project',
            storage
        },
        ProjectSlice.reducer
    ),
    //you can persist your auth reducer here similar to project reducer
    home: HomeSlice.reducer,
    theme: ThemeSlice.reducer,
    createproject: CreateProjectSlice.reducer,
})
// const middleware = routerMiddleware(history);

const middleware = [
    ...CoreModules.getDefaultMiddleware({ serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
    }, }),
    // add any other middleware here
  ];

export const store = CoreModules.configureStore({
    reducer: reducers,
    middleware: middleware

})

export const persistor = persistStore(store)
