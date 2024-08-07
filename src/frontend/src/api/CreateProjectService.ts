import axios from 'axios';
import { API } from '@/api';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import {
  ProjectDetailsModel,
  FormCategoryListModel,
  OrganisationListModel,
} from '@/models/createproject/createProjectModel';
import { CommonActions } from '@/store/slices/CommonSlice';
import { ValidateCustomFormResponse } from '@/store/types/ICreateProject';
import { isStatusSuccess } from '@/utilfunctions/commonUtils';

const CreateProjectService = (
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

    let projectId: null | number = null;
    try {
      // halt project creation if any api call fails
      let hasAPISuccess = false;

      const postNewProjectDetails = await API.post(url, projectData);
      hasAPISuccess = isStatusSuccess(postNewProjectDetails.status);

      const projectCreateResp: ProjectDetailsModel = postNewProjectDetails.data;
      await dispatch(CreateProjectActions.PostProjectDetails(projectCreateResp));

      if (!hasAPISuccess) {
        throw new Error(`Request failed with status ${projectCreateResp.status}`);
      }
      projectId = projectCreateResp.id;

      // Submit task boundaries
      hasAPISuccess = await dispatch(
        UploadTaskAreasService(
          `${import.meta.env.VITE_API_URL}/projects/${projectId}/upload-task-boundaries`,
          taskAreaGeojson,
        ),
      );

      if (!hasAPISuccess) {
        throw new Error(`Request failed`);
      }

      // Upload data extract
      let extractResponse;
      if (isOsmExtract) {
        // Generated extract from raw-data-api
        extractResponse = await API.get(
          `${import.meta.env.VITE_API_URL}/projects/data-extract-url/?project_id=${projectId}&url=${
            projectData.data_extract_url
          }`,
        );
      } else if (dataExtractFile) {
        // Custom data extract from user
        const dataExtractFormData = new FormData();
        dataExtractFormData.append('custom_extract_file', dataExtractFile);
        extractResponse = await API.post(
          `${import.meta.env.VITE_API_URL}/projects/upload-custom-extract/?project_id=${projectId}`,
          dataExtractFormData,
        );
      }
      hasAPISuccess = isStatusSuccess(extractResponse.status);

      if (!hasAPISuccess) {
        throw new Error(`Request failed with status ${extractResponse.status}`);
      }

      // Generate project files
      const generateProjectFile = await dispatch(
        GenerateProjectFilesService(
          `${import.meta.env.VITE_API_URL}/projects/${projectId}/generate-project-data`,
          projectData,
          formUpload,
        ),
      );

      hasAPISuccess = generateProjectFile;
      if (!hasAPISuccess) {
        throw new Error(`Request failed`);
      }
      dispatch(CreateProjectActions.GenerateProjectError(false));
      // dispatch(CreateProjectActions.CreateProjectLoading(false));
    } catch (error: any) {
      if (projectId) {
        await dispatch(DeleteProjectService(`${import.meta.env.VITE_API_URL}/projects/${projectId}`, false));
      }

      await dispatch(CreateProjectActions.GenerateProjectError(true));
      dispatch(
        CommonActions.SetSnackBar({
          open: true,
          message: JSON.stringify(error?.response?.data?.detail) || 'Something went wrong. Please try again.',
          variant: 'error',
          duration: 2000,
        }),
      );
      dispatch(CreateProjectActions.CreateProjectLoading(false));
    } finally {
      dispatch(CommonActions.SetLoading(false));
    }
  };
};

const FormCategoryService = (url: string) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GetFormCategoryLoading(true));

    const getFormCategoryList = async (url: string) => {
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

const UploadTaskAreasService = (url: string, filePayload: any, projectData: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.UploadAreaLoading(true));
    const postUploadArea = async (url: string, filePayload: any) => {
      let isAPISuccess = true;
      try {
        const areaFormData = new FormData();
        areaFormData.append('task_geojson', filePayload);
        const postNewProjectDetails = await axios.post(url, areaFormData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        isAPISuccess = isStatusSuccess(postNewProjectDetails.status);

        if (isAPISuccess) {
          await dispatch(CreateProjectActions.UploadAreaLoading(false));
          await dispatch(CreateProjectActions.PostUploadAreaSuccess(postNewProjectDetails.data));
        } else {
          throw new Error(`Request failed with status ${postNewProjectDetails.status}`);
        }
      } catch (error: any) {
        isAPISuccess = false;
        await dispatch(CreateProjectActions.GenerateProjectError(true));
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
      return isAPISuccess;
    };

    return await postUploadArea(url, filePayload);
  };
};

const GenerateProjectFilesService = (url: string, projectData: any, formUpload: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GenerateProjectLoading(true));
    dispatch(CommonActions.SetLoading(true));

    const postUploadArea = async (url, projectData: any, formUpload) => {
      let isAPISuccess = true;
      try {
        let response;

        if (projectData.form_ways === 'custom_form') {
          // TODO move form upload to a separate service / endpoint?
          const generateApiFormData = new FormData();
          generateApiFormData.append('xls_form_upload', formUpload);
          response = await axios.post(url, generateApiFormData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });
        } else {
          response = await axios.post(url, {});
        }
        isAPISuccess = isStatusSuccess(response.status);
        if (!isAPISuccess) {
          throw new Error(`Request failed with status ${response.status}`);
        }

        await dispatch(CreateProjectActions.GenerateProjectLoading(false));
        dispatch(CommonActions.SetLoading(false));
        // Trigger the watcher and redirect after success
        await dispatch(CreateProjectActions.GenerateProjectSuccess(true));
      } catch (error: any) {
        isAPISuccess = false;
        dispatch(CommonActions.SetLoading(false));
        await dispatch(CreateProjectActions.GenerateProjectError(true));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: JSON.stringify(error?.response?.data?.detail),
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(CreateProjectActions.GenerateProjectLoading(false));
      }
      return isAPISuccess;
    };

    return await postUploadArea(url, projectData, formUpload);
  };
};

const OrganisationService = (url: string) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GetOrganisationListLoading(true));

    const getOrganisationList = async (url: string) => {
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

const GetDividedTaskFromGeojson = (url: string, projectData: Record<string, any>) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetDividedTaskFromGeojsonLoading(true));

    const getDividedTaskFromGeojson = async (url: string, projectData: Record<string, any>) => {
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

const GetIndividualProjectDetails = (url: string) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsLoading(true));

    const getIndividualProjectDetails = async (url: string) => {
      try {
        const getIndividualProjectDetailsResponse = await axios.get(url);
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

    await getIndividualProjectDetails(url);
  };
};

const TaskSplittingPreviewService = (
  url: string,
  projectAoiFile: any,
  no_of_buildings: string,
  dataExtractFile: any,
) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.GetTaskSplittingPreviewLoading(true));

    const getTaskSplittingGeojson = async (url: string, projectAoiFile: any, dataExtractFile: any) => {
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
const PatchProjectDetails = (url: string, projectData: Record<string, any>) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetPatchProjectDetailsLoading(true));

    const patchProjectDetails = async (url: string, projectData: Record<string, any>) => {
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

const PostFormUpdate = (url: string, projectData: Record<string, any>) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetPostFormUpdateLoading(true));

    const postFormUpdate = async (url: string, projectData: Record<string, any>) => {
      try {
        const formFormData = new FormData();
        formFormData.append('xform_id', projectData.xformId);
        formFormData.append('category', projectData.category);
        formFormData.append('upload', projectData.upload);

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
const EditProjectBoundaryService = (url: string, geojsonUpload: any, dimension: any) => {
  return async (dispatch) => {
    dispatch(CreateProjectActions.SetEditProjectBoundaryServiceLoading(true));

    const postFormUpdate = async (url: string, geojsonUpload: any, dimension: any) => {
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

const ValidateCustomForm = (url: string, formUpload: any) => {
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
            message: error?.response?.data?.detail || 'Something Went Wrong',
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

const DeleteProjectService = (url: string, hasRedirect: boolean = true) => {
  return async (dispatch) => {
    const deleteProject = async (url: string) => {
      try {
        await API.delete(url);
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: `Project deleted. ${hasRedirect && 'Redirecting...'}`,
            variant: 'success',
            duration: 2000,
          }),
        );
        // Redirect to homepage
        if (hasRedirect) {
          setTimeout(() => {
            window.location.href = '/';
          }, 2000);
        }
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
  GenerateProjectFilesService,
  OrganisationService,
  GetDividedTaskFromGeojson,
  TaskSplittingPreviewService,
  GetIndividualProjectDetails,
  PatchProjectDetails,
  PostFormUpdate,
  EditProjectBoundaryService,
  ValidateCustomForm,
  DeleteProjectService,
};
