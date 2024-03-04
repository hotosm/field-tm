import axios from 'axios';
import { API } from '@/api';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import {
  ProjectDetailsModel,
  FormCategoryListModel,
  OrganisationListModel,
} from '@/models/createproject/createProjectModel';
import { CommonActions } from '@/store/slices/CommonSlice';
import { ValidateCustomFormResponse } from 'store/types/ICreateProject';
import { task_split_type } from '@/types/enums';

const CreateProjectService: Function = (
  url: string,
  projectData: any,
  taskAreaGeojson: any,
  formUpload: any,
  dataExtractFile: any,
  isOsmExtract: boolean,
) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.CreateProjectLoading(true));
    dispatch(CommonActions.SetLoading(true));

    const postCreateProjectDetails = async (url, projectData, taskAreaGeojson, formUpload) => {
      try {
        // Create project
        const postNewProjectDetails = await axios.post(url, projectData);
        const resp: ProjectDetailsModel = postNewProjectDetails.data;
        await dispatch(CreateProjectActions.PostProjectDetails(resp));

        // Submit task boundaries
        await dispatch(
          UploadTaskAreasService(
            `${import.meta.env.VITE_API_URL}/projects/${resp.id}/upload-task-boundaries`,
            taskAreaGeojson,
          ),
        );

        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Project Successfully Created Now Generating QR For Project',
            variant: 'success',
            duration: 2000,
          }),
        );

        if (isOsmExtract) {
          // Upload data extract generated from raw-data-api
          const response = await axios.get(
            `${import.meta.env.VITE_API_URL}/projects/data-extract-url/?project_id=${resp.id}&url=${
              projectData.data_extract_url
            }`,
          );
        } else if (dataExtractFile) {
          // Upload custom data extract from user
          const dataExtractFormData = new FormData();
          dataExtractFormData.append('custom_extract_file', dataExtractFile);
          const response = await axios.post(
            `${import.meta.env.VITE_API_URL}/projects/upload-custom-extract/?project_id=${resp.id}`,
            dataExtractFormData,
          );
        }

        // Generate QR codes
        await dispatch(
          GenerateProjectQRService(
            `${import.meta.env.VITE_API_URL}/projects/${resp.id}/generate-project-data`,
            projectData,
            formUpload,
          ),
        );

        dispatch(CommonActions.SetLoading(false));
        dispatch(CreateProjectActions.CreateProjectLoading(true));
      } catch (error: any) {
        dispatch(CommonActions.SetLoading(false));
        dispatch(CreateProjectActions.CreateProjectLoading(true));

        // Added Snackbar toast for error message
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: JSON.stringify(error?.response?.data?.detail) || 'Something went wrong.',
            variant: 'error',
            duration: 2000,
          }),
        );
        //END
        dispatch(CreateProjectActions.CreateProjectLoading(false));
      } finally {
        dispatch(CreateProjectActions.CreateProjectLoading(false));
      }
    };

    await postCreateProjectDetails(url, projectData, taskAreaGeojson, formUpload);
  };
};
const FormCategoryService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GetFormCategoryLoading(true));

    const getFormCategoryList = async (url) => {
      try {
        const getFormCategoryListResponse = await axios.get(url);
        const resp: FormCategoryListModel = getFormCategoryListResponse.data;
        dispatch(CreateProjectActions.GetFormCategoryList(resp));
      } catch (error) {
        dispatch(CreateProjectActions.GetFormCategoryListLoading(false));
      }
    };

    await getFormCategoryList(url);
  };
};
const UploadTaskAreasService: Function = (url: string, filePayload: any, projectData: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.UploadAreaLoading(true));
    const postUploadArea = async (url, filePayload) => {
      try {
        const areaFormData = new FormData();
        areaFormData.append('task_geojson', filePayload);
        const postNewProjectDetails = await axios.post(url, areaFormData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        // const resp: UploadAreaDetailsModel = postNewProjectDetails.data;
        await dispatch(CreateProjectActions.UploadAreaLoading(false));
        await dispatch(CreateProjectActions.PostUploadAreaSuccess(postNewProjectDetails.data));
      } catch (error: any) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: JSON.stringify(error?.response?.data?.detail) || 'Something Went Wrong.',
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(CreateProjectActions.UploadAreaLoading(false));
      }
    };

    await postUploadArea(url, filePayload);
  };
};
const GenerateProjectQRService: Function = (url: string, projectData: any, formUpload: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GenerateProjectQRLoading(true));
    dispatch(CommonActions.SetLoading(true));

    const postUploadArea = async (url, projectData: any, formUpload) => {
      try {
        let postNewProjectDetails;

        if (projectData.form_ways === 'custom_form') {
          // TODO move form upload to a separate service / endpoint?
          const generateApiFormData = new FormData();
          generateApiFormData.append('xls_form_upload', formUpload);
          postNewProjectDetails = await axios.post(url, generateApiFormData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });
        } else {
          postNewProjectDetails = await axios.post(url, {});
        }

        const resp: string = postNewProjectDetails.data;
        await dispatch(CreateProjectActions.GenerateProjectQRLoading(false));
        dispatch(CommonActions.SetLoading(false));
        await dispatch(CreateProjectActions.GenerateProjectQRSuccess(resp));
      } catch (error: any) {
        dispatch(CommonActions.SetLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: JSON.stringify(error?.response?.data?.detail),
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(CreateProjectActions.GenerateProjectQRLoading(false));
      }
    };

    await postUploadArea(url, projectData, formUpload);
  };
};

const OrganisationService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GetOrganisationListLoading(true));

    const getOrganisationList = async (url) => {
      try {
        const getOrganisationListResponse = await axios.get(url);
        const resp: OrganisationListModel = getOrganisationListResponse.data;
        dispatch(CreateProjectActions.GetOrganisationList(resp));
      } catch (error) {
        dispatch(CreateProjectActions.GetOrganisationListLoading(false));
      }
    };

    await getOrganisationList(url);
  };
};

const GenerateProjectLog: Function = (url: string, params: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GenerateProjectLogLoading(true));

    const getGenerateProjectLog = async (url, params) => {
      try {
        const getGenerateProjectLogResponse = await axios.get(url, { params });
        const resp: OrganisationListModel = getGenerateProjectLogResponse.data;
        dispatch(CreateProjectActions.SetGenerateProjectLog(resp));
      } catch (error) {
        dispatch(CreateProjectActions.GenerateProjectLogLoading(false));
      }
    };

    await getGenerateProjectLog(url, params);
  };
};
const GetDividedTaskFromGeojson: Function = (url: string, projectData: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetDividedTaskFromGeojsonLoading(true));

    const getDividedTaskFromGeojson = async (url, projectData) => {
      try {
        const dividedTaskFormData = new FormData();
        dividedTaskFormData.append('project_geojson', projectData.geojson);
        dividedTaskFormData.append('dimension', projectData.dimension);
        const getGetDividedTaskFromGeojsonResponse = await axios.post(url, dividedTaskFormData);
        const resp: OrganisationListModel = getGetDividedTaskFromGeojsonResponse.data;
        dispatch(CreateProjectActions.SetIsTasksGenerated({ key: 'divide_on_square', value: true }));
        dispatch(CreateProjectActions.SetIsTasksGenerated({ key: 'task_splitting_algorithm', value: false }));
        dispatch(CreateProjectActions.SetDividedTaskGeojson(resp));
        dispatch(CreateProjectActions.SetDividedTaskFromGeojsonLoading(false));
      } catch (error) {
        dispatch(CreateProjectActions.SetDividedTaskFromGeojsonLoading(false));
      } finally {
        dispatch(CreateProjectActions.SetDividedTaskFromGeojsonLoading(false));
      }
    };

    await getDividedTaskFromGeojson(url, projectData);
  };
};

const GetIndividualProjectDetails: Function = (url: string, projectData: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsLoading(true));

    const getIndividualProjectDetails = async (url, projectData) => {
      try {
        const getIndividualProjectDetailsResponse = await axios.get(url, { params: projectData });
        const resp: ProjectDetailsModel = getIndividualProjectDetailsResponse.data;
        const formattedOutlineGeojson = { type: 'FeatureCollection', features: [{ ...resp.outline_geojson, id: 1 }] };
        const modifiedResponse = {
          ...resp,
          name: resp.project_info?.name,
          description: resp.project_info?.description,
          short_description: resp.project_info?.short_description,
          outline_geojson: formattedOutlineGeojson,
          per_task_instructions: resp.project_info?.per_task_instructions,
        };

        dispatch(CreateProjectActions.SetIndividualProjectDetails(modifiedResponse));
        dispatch(CreateProjectActions.SetIndividualProjectDetailsLoading(false));
      } catch (error) {
        dispatch(CreateProjectActions.SetIndividualProjectDetailsLoading(false));
      } finally {
        dispatch(CreateProjectActions.SetIndividualProjectDetailsLoading(false));
      }
    };

    await getIndividualProjectDetails(url, projectData);
  };
};

const TaskSplittingPreviewService: Function = (
  url: string,
  projectAoiFile: any,
  no_of_buildings: string,
  dataExtractFile: any,
) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GetTaskSplittingPreviewLoading(true));

    const getTaskSplittingGeojson = async (url, projectAoiFile, dataExtractFile) => {
      try {
        const taskSplittingFileFormData = new FormData();
        taskSplittingFileFormData.append('project_geojson', projectAoiFile);
        taskSplittingFileFormData.append('no_of_buildings', no_of_buildings);
        // Only include data extract if custom extract uploaded
        if (dataExtractFile) {
          taskSplittingFileFormData.append('extract_geojson', dataExtractFile);
        }

        const getTaskSplittingResponse = await axios.post(url, taskSplittingFileFormData);
        const resp: OrganisationListModel = getTaskSplittingResponse.data;
        if (resp?.features && resp?.features.length < 1) {
          // Don't update geometry if splitting failed
          // TODO display error to user, perhaps there is not osm data here?
          return;
        }
        dispatch(CreateProjectActions.SetIsTasksGenerated({ key: 'divide_on_square', value: false }));
        dispatch(CreateProjectActions.SetIsTasksGenerated({ key: 'task_splitting_algorithm', value: true }));
        dispatch(CreateProjectActions.GetTaskSplittingPreview(resp));
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Task generation failed. Please try again',
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(CreateProjectActions.GetTaskSplittingPreviewLoading(false));
      } finally {
        dispatch(CreateProjectActions.GetTaskSplittingPreviewLoading(false));
      }
    };

    await getTaskSplittingGeojson(url, projectAoiFile, dataExtractFile);
  };
};
const PatchProjectDetails: Function = (url: string, projectData: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetPatchProjectDetailsLoading(true));

    const patchProjectDetails = async (url, projectData) => {
      try {
        const getIndividualProjectDetailsResponse = await axios.patch(url, projectData);
        const resp: ProjectDetailsModel = getIndividualProjectDetailsResponse.data;
        // dispatch(CreateProjectActions.SetIndividualProjectDetails(modifiedResponse));
        dispatch(CreateProjectActions.SetPatchProjectDetails(resp));
        dispatch(CreateProjectActions.SetPatchProjectDetailsLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Project Successfully Edited',
            variant: 'success',
            duration: 2000,
          }),
        );
      } catch (error) {
        dispatch(CreateProjectActions.SetPatchProjectDetailsLoading(false));
      } finally {
        dispatch(CreateProjectActions.SetPatchProjectDetailsLoading(false));
      }
    };

    await patchProjectDetails(url, projectData);
  };
};
const PostFormUpdate: Function = (url: string, projectData: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetPostFormUpdateLoading(true));

    const postFormUpdate = async (url, projectData) => {
      try {
        const formFormData = new FormData();
        formFormData.append('project_id', projectData.project_id);
        if (projectData.category) {
          formFormData.append('category', projectData.category);
        }
        if (projectData.upload) {
          formFormData.append('upload', projectData.upload);
        }
        const postFormUpdateResponse = await axios.post(url, formFormData);
        const resp: ProjectDetailsModel = postFormUpdateResponse.data;
        // dispatch(CreateProjectActions.SetIndividualProjectDetails(modifiedResponse));
        // dispatch(CreateProjectActions.SetPostFormUpdate(resp));
        dispatch(CreateProjectActions.SetPostFormUpdateLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Form Successfully Updated',
            variant: 'success',
            duration: 2000,
          }),
        );
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: error?.response?.data?.detail || 'Failed to update Form',
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(CreateProjectActions.SetPostFormUpdateLoading(false));
      } finally {
        dispatch(CreateProjectActions.SetPostFormUpdateLoading(false));
      }
    };

    await postFormUpdate(url, projectData);
  };
};
const EditProjectBoundaryService: Function = (url: string, geojsonUpload: any, dimension: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetEditProjectBoundaryServiceLoading(true));

    const postFormUpdate = async (url, geojsonUpload, dimension) => {
      try {
        const editBoundaryFormData = new FormData();
        editBoundaryFormData.append('project_geojson', geojsonUpload);
        if (dimension) {
          editBoundaryFormData.append('dimension', dimension);
        }
        const postBoundaryUpdateResponse = await axios.post(url, editBoundaryFormData);
        const resp: unknown = postBoundaryUpdateResponse.data;
        // dispatch(CreateProjectActions.SetIndividualProjectDetails(modifiedResponse));
        // dispatch(CreateProjectActions.SetPostFormUpdate(resp));
        dispatch(CreateProjectActions.SetEditProjectBoundaryServiceLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Project Boundary Successfully Updated',
            variant: 'success',
            duration: 2000,
          }),
        );
      } catch (error) {
        dispatch(CreateProjectActions.SetEditProjectBoundaryServiceLoading(false));
      } finally {
        dispatch(CreateProjectActions.SetEditProjectBoundaryServiceLoading(false));
      }
    };

    await postFormUpdate(url, geojsonUpload, dimension);
  };
};

const ValidateCustomForm: Function = (url: string, formUpload: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.ValidateCustomFormLoading(true));

    const validateCustomForm = async (url: any, formUpload: any) => {
      try {
        const formUploadFormData = new FormData();
        formUploadFormData.append('form', formUpload);

        const getTaskSplittingResponse = await axios.post(url, formUploadFormData);
        const resp: ValidateCustomFormResponse = getTaskSplittingResponse.data;
        dispatch(CreateProjectActions.ValidateCustomForm(resp));
        dispatch(CreateProjectActions.ValidateCustomFormLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: JSON.stringify(resp.message),
            variant: 'success',
            duration: 2000,
          }),
        );
        dispatch(CreateProjectActions.SetCustomFileValidity(true));
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: JSON.stringify(error.response.data.detail) || 'Something Went Wrong',
            variant: 'error',
            duration: 5000,
          }),
        );
        dispatch(CreateProjectActions.ValidateCustomFormLoading(false));
        dispatch(CreateProjectActions.SetCustomFileValidity(false));
      } finally {
        dispatch(CreateProjectActions.ValidateCustomFormLoading(false));
      }
    };

    await validateCustomForm(url, formUpload);
  };
};

const DeleteProjectService: Function = (url: string) => {
  return async (dispatch) => {
    const deleteProject = async (url: string) => {
      try {
        await API.delete(url);
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Project deleted. Redirecting...',
            variant: 'success',
            duration: 2000,
          }),
        );
        // Redirect to homepage
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } catch (error) {
        if (error.response.status === 404) {
          dispatch(
            CommonActions.SetSnackBar({
              open: true,
              message: 'Project already deleted',
              variant: 'success',
              duration: 2000,
            }),
          );
        } else {
        }
      }
    };

    await deleteProject(url);
  };
};

export {
  UploadTaskAreasService,
  CreateProjectService,
  FormCategoryService,
  GenerateProjectQRService,
  OrganisationService,
  GenerateProjectLog,
  GetDividedTaskFromGeojson,
  TaskSplittingPreviewService,
  GetIndividualProjectDetails,
  PatchProjectDetails,
  PostFormUpdate,
  EditProjectBoundaryService,
  ValidateCustomForm,
  DeleteProjectService,
};
