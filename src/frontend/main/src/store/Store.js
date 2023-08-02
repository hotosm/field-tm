import HomeSlice from './slices/HomeSlice';
import ThemeSlice from './slices/ThemeSlice';
// import projectSlice from 'map/Project';
import CoreModules from '../shared/CoreModules';
import { persistStore, FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import ProjectSlice from './slices/ProjectSlice';
import CreateProjectSlice from './slices/CreateProjectSlice';
import CommonSlice from './slices/CommonSlice';
import LoginSlice from './slices/LoginSlice';
import OrganizationSlice from './slices/organizationSlice.ts';
import SubmissionSlice from './slices/SubmissionSlice.ts';
import TaskSlice from './slices/TaskSlice.ts';
import { persistReducer } from 'redux-persist';

export default function persist(key, whitelist, reducer) {
  return persistReducer(
    {
      key,
      storage,
      whitelist,
    },
    reducer,
  );
}

const reducers = CoreModules.combineReducers({
  project: persist('project', ['project', 'projectInfo'], ProjectSlice.reducer),
  login: persist('login', ['loginToken', 'authDetails'], LoginSlice.reducer),
  //you can persist your auth reducer here similar to project reducer
  home: HomeSlice.reducer,
  theme: ThemeSlice.reducer,
  createproject: CreateProjectSlice.reducer,
  organization: OrganizationSlice.reducer,
  // added common slice in order to handle all the common things like snackbar etc
  common: CommonSlice.reducer,
  submission: SubmissionSlice.reducer,
  task: TaskSlice.reducer,
});

export const store = CoreModules.configureStore({
  reducer: reducers,
  // middleware: [],
  middleware: CoreModules.getDefaultMiddleware({
    serializableCheck: false,
  }),
});

export const persistor = persistStore(store);
