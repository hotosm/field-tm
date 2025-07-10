import axios, { AxiosResponse } from 'axios';
import { API } from '@/api';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import {
  ProjectDetailsModel,
  FormCategoryListModel,
  OrganisationListModel,
  splittedGeojsonType,
} from '@/models/createproject/createProjectModel';
import { CommonActions } from '@/store/slices/CommonSlice';
import { isStatusSuccess } from '@/utilfunctions/commonUtils';
import { AppDispatch } from '@/store/Store';
import isEmpty from '@/utilfunctions/isEmpty';
import { NavigateFunction } from 'react-router-dom';
import { ProjectDetailsTypes } from '@/store/types/ICreateProject';

const VITE_API_URL = import.meta.env.VITE_API_URL;

export const GetBasicProjectDetails = (url: string) => {
  return async (dispatch: AppDispatch) => {
    try {
      dispatch(CreateProjectActions.GetBasicProjectDetailsLoading(true));
      const response: AxiosResponse<{ id: number } & ProjectDetailsTypes> = await axios.get(url);
      const { id, name, short_description, description, organisation_id, outline } = response.data;
      dispatch(
        CreateProjectActions.SetBasicProjectDetails({
          id,
          name,
          short_description,
          description,
          organisation_id,
          outline,
        }),
      );
    } catch (error) {
      dispatch(
        CommonActions.SetSnackBar({
          message: JSON.stringify(error?.response?.data?.detail) || 'Error fetching basic project details',
        }),
      );
    } finally {
      dispatch(CreateProjectActions.GetBasicProjectDetailsLoading(false));
    }
  };
};

export const CreateDraftProjectService = (
  url: string,
  payload: Record<string, any>,
  project_admins: string[],
  params: Record<string, any>,
  navigate: NavigateFunction,
  continueToNextStep: boolean,
) => {
  return async (dispatch: AppDispatch) => {
    try {
      dispatch(CreateProjectActions.CreateDraftProjectLoading({ loading: true, continue: continueToNextStep }));
      const response: AxiosResponse = await axios.post(url, payload, { params });

      if (!isEmpty(project_admins)) {
        const promises = project_admins?.map(async (sub: any) => {
          await dispatch(
            AssignProjectManager(`${VITE_API_URL}/projects/add-manager`, {
              sub,
              project_id: response.data.id as number,
            }),
          );
        });
        await Promise.all(promises);
      }

      dispatch(
        CommonActions.SetSnackBar({
          variant: 'success',
          message: 'Draft project created successfully',
        }),
      );
      const redirectTo = continueToNextStep ? `/create-project/${response.data.id}?step=2` : `/`;
      navigate(redirectTo);
    } catch (error) {
      dispatch(
        CommonActions.SetSnackBar({
          message: error?.response?.data?.detail || 'Failed to create draft project',
        }),
      );
    } finally {
      dispatch(CreateProjectActions.CreateDraftProjectLoading({ loading: false, continue: false }));
    }
  };
};

export const CreateProjectService = (
  url: string,
  id: number,
  projectData: Record<string, any>,
  project_admins,
  file: { taskSplitGeojsonFile: File; dataExtractGeojsonFile: File; xlsFormFile: File },
  combinedFeaturesCount: number,
  isEmptyDataExtract: boolean,
  navigate: NavigateFunction,
) => {
  return async (dispatch: AppDispatch) => {
    try {
      dispatch(CreateProjectActions.CreateProjectLoading(true));

      // 1. post project details
      try {
        await API.patch(url, projectData);
      } catch (error) {
        const errorResponse = error?.response?.data?.detail;
        const errorMessage =
          typeof errorResponse === 'string'
            ? errorResponse || 'Something went wrong. Please try again.'
            : `Following errors occurred while creating project: ${errorResponse?.map((err) => `\n${err?.msg}`)}`;

        dispatch(
          CommonActions.SetSnackBar({
            message: errorMessage,
          }),
        );
      }

      // 2. post task boundaries
      await dispatch(
        UploadTaskAreasService(`${VITE_API_URL}/projects/${id}/upload-task-boundaries`, file.taskSplitGeojsonFile),
      );

      // 3. upload data extract
      if (isEmptyDataExtract) {
        // manually set response as we don't call an API
      } else if (file.dataExtractGeojsonFile) {
        await dispatch(
          UploadDataExtractService(
            `${VITE_API_URL}/projects/upload-data-extract?project_id=${id}`,
            file.dataExtractGeojsonFile,
          ),
        );
      } else {
        dispatch(
          CommonActions.SetSnackBar({
            message: 'No data extract file or empty data extract file was set',
          }),
        );
      }

      // 4. upload form
      await dispatch(
        GenerateProjectFilesService(
          `${VITE_API_URL}/projects/${id}/generate-project-data`,
          projectData,
          file.xlsFormFile,
          combinedFeaturesCount,
        ),
      );

      // 5. assign project managers
      if (!isEmpty(project_admins)) {
        const promises = project_admins?.map(async (sub: any) => {
          await dispatch(
            AssignProjectManager(`${VITE_API_URL}/projects/add-manager`, {
              sub,
              project_id: id as number,
            }),
          );
        });
        await Promise.all(promises);
      }

      dispatch(
        CommonActions.SetSnackBar({
          message: 'Project Generation Completed. Redirecting...',
          variant: 'success',
          duration: 5000,
        }),
      );

      // Add 5-second delay to allow backend Entity generation to catch up
      const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
      await delay(5000);
      navigate(`/project/${id}`);
    } catch (error) {
      dispatch(
        CommonActions.SetSnackBar({
          message: error?.response?.data?.detail || 'Something went wrong. Please try again.',
        }),
      );
    } finally {
      dispatch(CreateProjectActions.CreateProjectLoading(false));
    }
  };
};

const CreateProjectServiceDeprecated = (
  url: string,
  projectData: any,
  taskAreaGeojson: any,
  formUpload: any,
  dataExtractFile: File,
  projectAdmins: number[],
  combinedFeaturesCount: number,
  isEmptyDataExtract: boolean,
) => {
  return async (dispatch: AppDispatch) => {
    dispatch(CreateProjectActions.CreateProjectLoading(true));
    dispatch(CommonActions.SetLoading(true));

    let projectId: null | number = null;
    try {
      let hasAPISuccess = false; // set to true if any of the APIs fails
      let postNewProjectDetails: AxiosResponse<ProjectDetailsModel> | null = null;

      // 1. post project details
      try {
        postNewProjectDetails = await API.post(url, projectData);
      } catch (error) {
        const errorResponse = error?.response?.data?.detail;
        const errorMessage =
          typeof errorResponse === 'string'
            ? errorResponse || 'Something went wrong. Please try again.'
            : `Following errors occurred while creating project: ${errorResponse?.map((err) => `\n${err?.msg}`)}`;

        dispatch(
          CommonActions.SetSnackBar({
            message: errorMessage,
          }),
        );
      }

      hasAPISuccess = !!postNewProjectDetails; // postNewProjectDetails is null if post project request fails
      if (!hasAPISuccess) throw new Error();

      const projectCreateResp: ProjectDetailsModel = postNewProjectDetails?.data!;
      projectId = projectCreateResp.id;
      dispatch(CreateProjectActions.PostProjectDetails(projectCreateResp));

      // 2. post task boundaries
      hasAPISuccess = await dispatch(
        UploadTaskAreasService(`${VITE_API_URL}/projects/${projectId}/upload-task-boundaries`, taskAreaGeojson),
      );
      if (!hasAPISuccess) throw new Error();

      // 3. upload data extract
      if (isEmptyDataExtract) {
        // manually set response as we don't call an API
      } else if (dataExtractFile) {
        hasAPISuccess = await dispatch(
          UploadDataExtractService(
            `${VITE_API_URL}/projects/upload-data-extract?project_id=${projectId}`,
            dataExtractFile,
          ),
        );
        if (!hasAPISuccess) throw new Error();
      } else {
        dispatch(
          CommonActions.SetSnackBar({
            message: 'No dataExtractFile or EmptyDataExtractwas set',
          }),
        );
        throw new Error();
      }

      // 4. upload form
      const generateProjectFile = await dispatch(
        GenerateProjectFilesService(
          `${VITE_API_URL}/projects/${projectId}/generate-project-data`,
          projectData,
          formUpload,
          combinedFeaturesCount,
        ),
      );

      hasAPISuccess = generateProjectFile;
      if (!hasAPISuccess) throw new Error();

      // 5. assign project admins
      if (!isEmpty(projectAdmins)) {
        const promises = projectAdmins?.map(async (sub: any) => {
          await dispatch(
            AssignProjectManager(`${VITE_API_URL}/projects/add-manager`, { sub, project_id: projectId as number }),
          );
        });
        await Promise.all(promises);
      }

      dispatch(CreateProjectActions.GenerateProjectError(false));
    } catch (error: any) {
      if (projectId) {
        await dispatch(DeleteProjectService(`${VITE_API_URL}/projects/${projectId}`));
      }
      dispatch(CreateProjectActions.GenerateProjectError(true));
    } finally {
      dispatch(CreateProjectActions.CreateProjectLoading(false));
      dispatch(CommonActions.SetLoading(false));
    }
  };
};

const FormCategoryService = (url: string) => {
  return async (dispatch: AppDispatch) => {
    dispatch(CreateProjectActions.GetFormCategoryLoading(true));

    const getFormCategoryList = async (url: string) => {
      try {
        const getFormCategoryListResponse = await axios.get(url);
        const resp: FormCategoryListModel[] = getFormCategoryListResponse.data;
        dispatch(CreateProjectActions.GetFormCategoryList(resp));
      } catch (error) {
      } finally {
        dispatch(CreateProjectActions.GetFormCategoryLoading(false));
      }
    };

    await getFormCategoryList(url);
  };
};

const UploadTaskAreasService = (url: string, filePayload: any) => {
  return async (dispatch: AppDispatch) => {
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

        if (!isAPISuccess) {
          const msg = `Request failed with status ${postNewProjectDetails.status}`;
          console.error(msg);
          throw new Error(msg);
        }
      } catch (error: any) {
        isAPISuccess = false;
        await dispatch(CreateProjectActions.GenerateProjectError(true));
        dispatch(
          CommonActions.SetSnackBar({
            message: JSON.stringify(error?.response?.data?.detail) || 'Upload task area failed',
          }),
        );
      }
      return isAPISuccess;
    };

    return await postUploadArea(url, filePayload);
  };
};

const UploadDataExtractService = (url: string, file: any) => {
  return async (dispatch: AppDispatch) => {
    const postUploadDataExtract = async (url: string, file: any) => {
      let isAPISuccess = true;
      try {
        const dataExtractFormData = new FormData();
        dataExtractFormData.append('data_extract_file', file);
        await axios.post(url, dataExtractFormData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
      } catch (error: any) {
        isAPISuccess = false;
        dispatch(
          CommonActions.SetSnackBar({
            message: JSON.stringify(error?.response?.data?.detail) || 'Upload data extract failed',
          }),
        );
      }
      return isAPISuccess;
    };

    return await postUploadDataExtract(url, file);
  };
};

const GenerateProjectFilesService = (url: string, projectData: any, formUpload: any, combinedFeaturesCount: number) => {
  return async (dispatch: AppDispatch) => {
    dispatch(CreateProjectActions.GenerateProjectLoading(true));
    dispatch(CommonActions.SetLoading(true));

    try {
      const formData = new FormData();

      // Append xlsform
      formData.append('xlsform', formUpload);

      // Add combined features count
      formData.append('combined_features_count', combinedFeaturesCount.toString());

      const response = await axios.post(url, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (!isStatusSuccess(response.status)) {
        const msg = `Request failed with status ${response.status}`;
        console.error(msg);
        throw new Error(msg);
      }

      // If warning provided, then inform user
      const message = response.data?.message;
      if (message) {
        dispatch(CreateProjectActions.GenerateProjectWarning(message));
      }

      dispatch(CreateProjectActions.GenerateProjectSuccess(true));
      return true; // ✅ Return success
    } catch (error: any) {
      dispatch(CreateProjectActions.GenerateProjectError(true));
      dispatch(
        CommonActions.SetSnackBar({
          message: JSON.stringify(error?.response?.data?.detail),
        }),
      );
      return false; // ❌ Return failure
    } finally {
      dispatch(CreateProjectActions.GenerateProjectLoading(false));
      dispatch(CommonActions.SetLoading(false));
    }
  };
};

const OrganisationService = (url: string) => {
  return async (dispatch: AppDispatch) => {
    dispatch(CreateProjectActions.GetOrganisationListLoading(true));

    const getOrganisationList = async (url: string) => {
      try {
        const getOrganisationListResponse = await axios.get(url);
        const resp: OrganisationListModel[] = getOrganisationListResponse.data;
        dispatch(CreateProjectActions.GetOrganisationList(resp));
      } catch (error) {
      } finally {
        dispatch(CreateProjectActions.GetOrganisationListLoading(false));
      }
    };

    await getOrganisationList(url);
  };
};

const GetIndividualProjectDetails = (url: string) => {
  return async (dispatch: AppDispatch) => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsLoading(true));

    const getIndividualProjectDetails = async (url: string) => {
      try {
        const getIndividualProjectDetailsResponse = await axios.get(url);
        const resp: ProjectDetailsModel = getIndividualProjectDetailsResponse.data;
        const formattedOutlineGeojson = { type: 'FeatureCollection', features: [{ ...resp.outline, id: 1 }] };
        const modifiedResponse = {
          ...resp,
          name: resp.name,
          description: resp.description,
          short_description: resp.short_description,
          outline: formattedOutlineGeojson,
          per_task_instructions: resp.per_task_instructions,
        };

        dispatch(CreateProjectActions.SetIndividualProjectDetails(modifiedResponse));
      } catch (error) {
        if (error.response.status === 404) {
          dispatch(CommonActions.SetProjectNotFound(true));
        }
      } finally {
        dispatch(CreateProjectActions.SetIndividualProjectDetailsLoading(false));
      }
    };

    await getIndividualProjectDetails(url);
  };
};

const GetDividedTaskFromGeojson = (url: string, projectData: Record<string, any>) => {
  return async (dispatch: AppDispatch) => {
    dispatch(CreateProjectActions.GetTaskSplittingPreview(null));
    dispatch(CreateProjectActions.SetDividedTaskFromGeojsonLoading(true));

    const getDividedTaskFromGeojson = async (url: string, projectData: Record<string, any>) => {
      try {
        const dividedTaskFormData = new FormData();
        dividedTaskFormData.append('project_geojson', projectData.geojson);
        dividedTaskFormData.append('dimension_meters', projectData.dimension);
        const getGetDividedTaskFromGeojsonResponse = await axios.post(url, dividedTaskFormData);
        const resp: splittedGeojsonType = getGetDividedTaskFromGeojsonResponse.data;
        dispatch(CreateProjectActions.SetIsTasksSplit({ key: 'divide_on_square', value: true }));
        dispatch(CreateProjectActions.SetIsTasksSplit({ key: 'task_splitting_algorithm', value: false }));
        dispatch(CreateProjectActions.SetDividedTaskGeojson(resp));
      } catch (error) {
      } finally {
        dispatch(CreateProjectActions.SetDividedTaskFromGeojsonLoading(false));
      }
    };

    await getDividedTaskFromGeojson(url, projectData);
  };
};

const TaskSplittingPreviewService = (
  url: string,
  projectAoiFile: any,
  no_of_buildings: number,
  dataExtractFile: any,
) => {
  return async (dispatch: AppDispatch) => {
    dispatch(CreateProjectActions.SetDividedTaskGeojson(null));
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
        const resp: splittedGeojsonType = getTaskSplittingResponse.data;
        if (resp?.features && resp?.features.length < 1) {
          // Don't update geometry if splitting failed
          // TODO display error to user, perhaps there is not osm data here?
          return;
        }
        dispatch(CreateProjectActions.SetIsTasksSplit({ key: 'divide_on_square', value: false }));
        dispatch(CreateProjectActions.SetIsTasksSplit({ key: 'task_splitting_algorithm', value: true }));
        dispatch(CreateProjectActions.GetTaskSplittingPreview(resp));
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Task generation failed. Please try again',
          }),
        );
      } finally {
        dispatch(CreateProjectActions.GetTaskSplittingPreviewLoading(false));
      }
    };

    await getTaskSplittingGeojson(url, projectAoiFile, dataExtractFile);
  };
};
const PatchProjectDetails = (url: string, projectData: Record<string, any>) => {
  return async (dispatch: AppDispatch) => {
    dispatch(CreateProjectActions.SetPatchProjectDetailsLoading(true));

    const patchProjectDetails = async (url: string, projectData: Record<string, any>) => {
      try {
        const getIndividualProjectDetailsResponse = await axios.patch(url, projectData);
        const resp: ProjectDetailsModel = getIndividualProjectDetailsResponse.data;
        // dispatch(CreateProjectActions.SetIndividualProjectDetails(modifiedResponse));
        dispatch(CreateProjectActions.SetPatchProjectDetails(resp));
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Project Successfully Edited',
            variant: 'success',
          }),
        );
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Failed. Do you have permission to edit?',
          }),
        );
      } finally {
        dispatch(CreateProjectActions.SetPatchProjectDetailsLoading(false));
      }
    };

    await patchProjectDetails(url, projectData);
  };
};

const PostFormUpdate = (url: string, projectData: Record<string, any>) => {
  return async (dispatch: AppDispatch) => {
    dispatch(CreateProjectActions.SetPostFormUpdateLoading(true));

    const postFormUpdate = async (url: string, projectData: Record<string, any>) => {
      try {
        const formFormData = new FormData();
        formFormData.append('xform_id', projectData.xformId);
        // FIXME add back in capability to update osm_category
        // formFormData.append('category', projectData.osm_category);
        formFormData.append('xlsform', projectData.upload);

        const postFormUpdateResponse = await axios.post(url, formFormData);
        const resp: { message: string } = postFormUpdateResponse.data;
        // dispatch(CreateProjectActions.SetIndividualProjectDetails(modifiedResponse));
        // dispatch(CreateProjectActions.SetPostFormUpdate(resp));
        dispatch(
          CommonActions.SetSnackBar({
            message: resp.message,
            variant: 'success',
          }),
        );
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: error?.response?.data?.detail || 'Failed to update Form',
          }),
        );
      } finally {
        dispatch(CreateProjectActions.SetPostFormUpdateLoading(false));
      }
    };

    await postFormUpdate(url, projectData);
  };
};

const EditProjectBoundaryService = (url: string, geojsonUpload: any, dimension: any) => {
  return async (dispatch: AppDispatch) => {
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
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Project Boundary Successfully Updated',
            variant: 'success',
          }),
        );
      } catch (error) {
      } finally {
        dispatch(CreateProjectActions.SetEditProjectBoundaryServiceLoading(false));
      }
    };

    await postFormUpdate(url, geojsonUpload, dimension);
  };
};

const ValidateCustomForm = (url: string, formUpload: any, useOdkCollect: boolean) => {
  return async (dispatch: AppDispatch) => {
    dispatch(CreateProjectActions.ValidateCustomFormLoading(true));

    const validateCustomForm = async (url: any, formUpload: any) => {
      try {
        const formUploadFormData = new FormData();
        formUploadFormData.append('xlsform', formUpload);
        formUploadFormData.append('use_odk_collect', useOdkCollect.toString());

        const getTaskSplittingResponse = await axios.post(url, formUploadFormData);
        const resp = getTaskSplittingResponse.data;
        dispatch(
          CommonActions.SetSnackBar({
            message: JSON.stringify(resp.message),
            variant: 'success',
          }),
        );
        dispatch(CreateProjectActions.SetCustomFileValidity(true));
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: error?.response?.data?.detail || 'Something Went Wrong',
          }),
        );
        dispatch(CreateProjectActions.SetCustomFileValidity(false));
      } finally {
        dispatch(CreateProjectActions.ValidateCustomFormLoading(false));
      }
    };

    await validateCustomForm(url, formUpload);
  };
};

const DeleteProjectService = (url: string, navigate?: NavigateFunction) => {
  return async (dispatch: AppDispatch) => {
    const deleteProject = async (url: string) => {
      try {
        dispatch(CreateProjectActions.SetProjectDeletePending(true));
        await API.delete(url);
        dispatch(
          CommonActions.SetSnackBar({
            message: `Project deleted`,
            variant: 'success',
          }),
        );
        if (navigate) navigate('/');
      } catch (error) {
        if (error.response.status === 404) {
          dispatch(
            CommonActions.SetSnackBar({
              message: 'Project already deleted',
              variant: 'success',
            }),
          );
        }
      } finally {
        dispatch(CreateProjectActions.SetProjectDeletePending(false));
      }
    };

    await deleteProject(url);
  };
};

const AssignProjectManager = (url: string, params: { sub: number; project_id: number }) => {
  return async (dispatch: AppDispatch) => {
    const assignProjectManager = async () => {
      try {
        await axios.post(url, {}, { params });
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: error.response.data.detail || 'Could not assign project manager',
          }),
        );
      }
    };

    return await assignProjectManager();
  };
};

export {
  UploadTaskAreasService,
  CreateProjectServiceDeprecated,
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
