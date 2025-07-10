import { CreateProjectStateTypes, ProjectDetailsTypes } from '@/store/types/ICreateProject';
import { project_visibility, task_split_type } from '@/types/enums';
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
  formExampleList: [],
  formCategoryLoading: false,
  generateProjectLoading: false,
  generateProjectSuccess: false,
  generateProjectWarning: null,
  generateProjectError: false,
  organisationList: [],
  organisationListLoading: false,
  dividedTaskLoading: false,
  dividedTaskGeojson: null,
  formUpdateLoading: false,
  taskSplittingGeojsonLoading: false,
  taskSplittingGeojson: null,
  updateBoundaryLoading: false,
  drawnGeojson: null,
  drawToggle: false,
  validateCustomFormLoading: false,
  uploadAreaSelection: null,
  totalAreaSelection: null,
  taskSplittingMethod: null,
  dataExtractGeojson: null,
  createProjectValidations: {},
  isUnsavedChanges: false,
  canSwitchCreateProjectSteps: false,
  isTasksSplit: { divide_on_square: false, task_splitting_algorithm: false },
  isFgbFetching: false,
  toggleSplittedGeojsonEdit: false,
  customFileValidity: false,
  descriptionToFocus: null,
  isProjectDeletePending: false,
  splitGeojsonBySquares: null,
  splitGeojsonByAlgorithm: null,
  basicProjectDetailsLoading: false,
  basicProjectDetails: null,
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
    ClearCreateProjectFormData(state) {
      // state.projectDetailsResponse = null
      state.projectDetails = {
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
        visibility: project_visibility.PUBLIC,
        use_odk_collect: false,
      };
      state.totalAreaSelection = null;
      state.taskSplittingMethod = null;
      state.dataExtractGeojson = null;
      state.taskSplittingGeojson = null;
      state.drawnGeojson = null;
      state.isUnsavedChanges = false;
      state.uploadAreaSelection = null;
      state.dividedTaskGeojson = null;
      state.dividedTaskLoading = false;
      state.generateProjectSuccess = false;
      state.generateProjectWarning = null;
      state.generateProjectError = false;
      state.drawToggle = false;
    },
    GetFormCategoryLoading(state, action: PayloadAction<boolean>) {
      state.formCategoryLoading = action.payload;
    },
    GetFormCategoryList(state, action: PayloadAction<CreateProjectStateTypes['formExampleList']>) {
      state.formExampleList = action.payload;
    },
    SetIndividualProjectDetailsData(state, action) {
      state.projectDetails = action.payload;
    },
    GenerateProjectLoading(state, action: PayloadAction<boolean>) {
      state.generateProjectLoading = action.payload;
    },
    GenerateProjectSuccess(state, action: PayloadAction<boolean>) {
      state.generateProjectSuccess = action.payload;
    },
    GenerateProjectWarning(state, action: PayloadAction<string>) {
      state.generateProjectWarning = action.payload;
    },
    GenerateProjectError(state, action: PayloadAction<boolean>) {
      state.generateProjectError = action.payload;
    },
    GetOrganisationList(state, action: PayloadAction<CreateProjectStateTypes['organisationList']>) {
      state.organisationList = action.payload;
    },
    GetOrganisationListLoading(state, action: PayloadAction<boolean>) {
      state.organisationListLoading = action.payload;
    },
    SetDividedTaskGeojson(state, action: PayloadAction<CreateProjectStateTypes['dividedTaskGeojson']>) {
      state.dividedTaskGeojson = action.payload;
      state.splitGeojsonBySquares = action.payload;
    },
    SetDrawnGeojson(state, action) {
      state.drawnGeojson = action.payload;
    },
    SetDividedTaskFromGeojsonLoading(state, action: PayloadAction<boolean>) {
      state.dividedTaskLoading = action.payload;
    },
    //EDIT Project

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
    GetTaskSplittingPreview(state, action: PayloadAction<CreateProjectStateTypes['dividedTaskGeojson']>) {
      state.dividedTaskGeojson = action.payload;
      state.splitGeojsonByAlgorithm = action.payload;
    },
    SetEditProjectBoundaryServiceLoading(state, action: PayloadAction<boolean>) {
      state.updateBoundaryLoading = action.payload;
    },
    SetDrawToggle(state, action: PayloadAction<boolean>) {
      state.drawToggle = action.payload;
    },
    ValidateCustomFormLoading(state, action: PayloadAction<boolean>) {
      state.validateCustomFormLoading = action.payload;
    },
    SetUploadAreaSelection(state, action: PayloadAction<'upload_file' | 'draw'>) {
      state.uploadAreaSelection = action.payload;
    },
    SetTotalAreaSelection(state, action: PayloadAction<string | null>) {
      state.totalAreaSelection = action.payload;
    },
    SetTaskSplittingMethod(state, action: PayloadAction<task_split_type>) {
      state.taskSplittingMethod = action.payload;
    },
    setDataExtractGeojson(state, action) {
      state.dataExtractGeojson = action.payload;
    },
    SetIsUnsavedChanges(state, action: PayloadAction<boolean>) {
      state.isUnsavedChanges = action.payload;
    },
    SetCanSwitchCreateProjectSteps(state, action: PayloadAction<boolean>) {
      state.canSwitchCreateProjectSteps = action.payload;
    },
    SetIsTasksSplit(
      state,
      action: PayloadAction<{
        key: 'divide_on_square' | 'task_splitting_algorithm';
        value: boolean;
      }>,
    ) {
      state.isTasksSplit = {
        ...state.isTasksSplit,
        [action.payload.key]: action.payload.value,
      };
    },
    SetFgbFetchingStatus(state, action: PayloadAction<boolean>) {
      state.isFgbFetching = action.payload;
    },
    ClearProjectStepState(state, action) {
      state.dividedTaskGeojson = null;
      state.taskSplittingMethod = null;
      state.dataExtractGeojson = null;
      state.projectDetails = { ...action.payload, customLineUpload: null, customPolygonUpload: null };
    },
    SetToggleSplittedGeojsonEdit(state, action: PayloadAction<boolean>) {
      state.toggleSplittedGeojsonEdit = action.payload;
    },
    SetCustomFileValidity(state, action: PayloadAction<boolean>) {
      state.customFileValidity = action.payload;
    },
    SetDescriptionToFocus(state, action: PayloadAction<CreateProjectStateTypes['descriptionToFocus']>) {
      state.descriptionToFocus = action.payload;
    },
    SetProjectDeletePending(state, action: PayloadAction<boolean>) {
      state.isProjectDeletePending = action.payload;
    },
    GetBasicProjectDetailsLoading(state, action: PayloadAction<boolean>) {
      state.basicProjectDetailsLoading = action.payload;
    },
    SetBasicProjectDetails(
      state,
      action: PayloadAction<
        | ({ id: number } & Pick<
            ProjectDetailsTypes,
            'name' | 'short_description' | 'description' | 'organisation_id' | 'outline'
          >)
        | null
      >,
    ) {
      state.basicProjectDetails = action.payload;
    },
  },
});

export const CreateProjectActions = CreateProject.actions;
export default CreateProject.reducer;
