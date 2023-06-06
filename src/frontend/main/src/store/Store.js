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
import CommonSlice from "./slices/CommonSlice";
import LoginSlice from "./slices/LoginSlice";
import OrganizationSlice from "./slices/organizationSlice.ts"
import SubmissionSlice from "./slices/SubmissionSlice.ts"

const reducers = CoreModules.combineReducers({
    // project: persistReducer(
    //     {
    //         key: 'project',
    //         storage
    //     },
    //     ProjectSlice.reducer
    // ),
    project: ProjectSlice.reducer,
    login: persistReducer(
        {
            key: 'login',
            storage
        },
        LoginSlice.reducer
    ),
    //you can persist your auth reducer here similar to project reducer
    home: HomeSlice.reducer,
    theme: ThemeSlice.reducer,
    createproject: CreateProjectSlice.reducer,
    organization: OrganizationSlice.reducer,
    // added common slice in order to handle all the common things like snackbar etc
    common: CommonSlice.reducer,
    submission: SubmissionSlice.reducer
})
// const middleware = routerMiddleware(history);

// const middleware = [
//     ...CoreModules.getDefaultMiddleware({ serializableCheck: {
//         ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
//     }, }),
//     // add any other middleware here
//   ];

export const store = CoreModules.configureStore({
    reducer: reducers,
    // middleware: middleware

})

export const persistor = persistStore(store)
