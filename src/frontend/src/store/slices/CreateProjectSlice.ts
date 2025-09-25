import { CreateProjectStateTypes } from '@/store/types/ICreateProject';
import { project_visibility } from '@/types/enums';
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export const initialState: CreateProjectStateTypes = {
  editProjectDetails: { name: '', description: '', short_description: '' },
  editProjectResponse: null,
  projectDetails: {
    dimension: 10,
    no_of_buildings: 5,
    hashtags: [],
    name: '',
    short_description: '',
    odk_central_url: '',
    odk_central_user: '',
    odk_central_password: '',
    description: '',
    organisation_id: null,
    per_task_instructions: '',
    hasCustomTMS: false,
    custom_tms_url: '',
    project_admins: [],
    visibility: project_visibility.PUBLIC,
    use_odk_collect: false,
    includeCentroid: false,
  },
  projectDetailsResponse: null,
  createDraftProjectLoading: { loading: false, continue: false },
  createProjectLoading: false,
  projectDetailsLoading: false,
  editProjectDetailsLoading: false,
  formCategoryLoading: false,
  GenerateProjectFilesLoading: false,
  dividedTaskLoading: false,
  formUpdateLoading: false,
  taskSplittingGeojsonLoading: false,
  taskSplittingGeojson: null,
  validateCustomFormLoading: false,
  createProjectValidations: {},
  isUnsavedChanges: false,
  customFileValidity: false,
  isProjectDeletePending: false,
  splitGeojsonBySquares: null,
  splitGeojsonByAlgorithm: null,
  isODKCredentialsValid: false,
  ODKCredentialsValidating: false,
};

const CreateProject = createSlice({
  name: 'createproject',
  initialState: initialState,
  reducers: {
    CreateDraftProjectLoading(state, action: PayloadAction<CreateProjectStateTypes['createDraftProjectLoading']>) {
      state.createDraftProjectLoading = action.payload;
    },
    CreateProjectLoading(state, action: PayloadAction<boolean>) {
      state.createProjectLoading = action.payload;
    },
    PostProjectDetails(state, action) {
      state.projectDetailsResponse = action.payload;
    },
    GetFormCategoryLoading(state, action: PayloadAction<boolean>) {
      state.formCategoryLoading = action.payload;
    },
    GenerateProjectFilesLoading(state, action: PayloadAction<boolean>) {
      state.GenerateProjectFilesLoading = action.payload;
    },
    SetDividedTaskGeojson(state, action: PayloadAction<CreateProjectStateTypes['splitGeojsonBySquares']>) {
      state.splitGeojsonBySquares = action.payload;
    },
    SetDividedTaskFromGeojsonLoading(state, action: PayloadAction<boolean>) {
      state.dividedTaskLoading = action.payload;
    },
    SetIndividualProjectDetails(state, action) {
      state.editProjectDetails = action.payload;
    },
    SetIndividualProjectDetailsLoading(state, action: PayloadAction<boolean>) {
      state.projectDetailsLoading = action.payload;
    },
    SetPatchProjectDetails(state, action) {
      state.editProjectResponse = action.payload;
    },
    SetPatchProjectDetailsLoading(state, action: PayloadAction<boolean>) {
      state.editProjectDetailsLoading = action.payload;
    },
    SetPostFormUpdateLoading(state, action: PayloadAction<boolean>) {
      state.formUpdateLoading = action.payload;
    },
    GetTaskSplittingPreviewLoading(state, action: PayloadAction<boolean>) {
      state.taskSplittingGeojsonLoading = action.payload;
    },
    GetTaskSplittingPreview(state, action: PayloadAction<CreateProjectStateTypes['splitGeojsonByAlgorithm']>) {
      state.splitGeojsonByAlgorithm = action.payload;
    },
    ValidateCustomFormLoading(state, action: PayloadAction<boolean>) {
      state.validateCustomFormLoading = action.payload;
    },
    SetCustomFileValidity(state, action: PayloadAction<boolean>) {
      state.customFileValidity = action.payload;
    },
    SetProjectDeletePending(state, action: PayloadAction<boolean>) {
      state.isProjectDeletePending = action.payload;
    },
    SetODKCredentialsValid(state, action: PayloadAction<boolean>) {
      state.isODKCredentialsValid = action.payload;
    },
    SetODKCredentialsValidating(state, action: PayloadAction<boolean>) {
      state.ODKCredentialsValidating = action.payload;
    },
  },
});

export const CreateProjectActions = CreateProject.actions;
export default CreateProject.reducer;
