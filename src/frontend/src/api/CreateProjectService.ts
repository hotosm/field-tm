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
import { UnassignUserFromProject } from '@/api/Project';

const VITE_API_URL = import.meta.env.VITE_API_URL;

export const GetBasicProjectDetails = (url: string) => {
  return async (dispatch: AppDispatch) => {
    try {
      dispatch(CreateProjectActions.GetBasicProjectDetailsLoading(true));
      const response: AxiosResponse<{ id: number } & ProjectDetailsTypes> = await axios.get(url);
      const { id, name, short_description, description, organisation_id, outline, hashtags, organisation_name } =
        response.data;
      dispatch(
        CreateProjectActions.SetBasicProjectDetails({
          id,
          name,
          short_description,
          description,
          organisation_id,
          outline,
          hashtags,
          organisation_name,
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
  payload: { projectPayload: Record<string, any>; odkPayload: Record<string, any> | null; project_admins: string[] },
  navigate: NavigateFunction,
  continueToNextStep: boolean,
) => {
  return async (dispatch: AppDispatch) => {
    let projectId: number | null = null;
    try {
      dispatch(CreateProjectActions.CreateDraftProjectLoading({ loading: true, continue: continueToNextStep }));

      const { projectPayload, odkPayload, project_admins } = payload;

      // 1. Create draft project
      const response: AxiosResponse = await axios.post(url, projectPayload, {
        params: { org_id: projectPayload.organisation_id },
      });

      projectId = response.data.id;

      // 2. Add ODK details (to create project in ODK  patch createProject even if default ODK creds used)
      await axios.patch(`${VITE_API_URL}/projects`, odkPayload || {}, {
        params: { project_id: projectId as number },
      });

      // 3. Add project admins
      if (!isEmpty(project_admins)) {
        try {
          const promises = project_admins?.map(async (sub: any) => {
            await dispatch(
              AssignProjectManager(`${VITE_API_URL}/projects/add-manager`, {
                sub,
                project_id: projectId as number,
              }),
            );
          });
          await Promise.all(promises);
        } catch (error) {
          dispatch(
            CommonActions.SetSnackBar({
              message: error?.response?.data?.detail || 'Failed to add project admin',
            }),
          );
        }
      }

      dispatch(
        CommonActions.SetSnackBar({
          variant: 'success',
          message: 'Draft project created successfully',
        }),
      );
      const redirectTo = continueToNextStep ? `/create-project/${projectId}?step=2` : `/`;
      navigate(redirectTo);
    } catch (error) {
      dispatch(
        CommonActions.SetSnackBar({
          message: error?.response?.data?.detail || 'Failed to create draft project',
        }),
      );

      if (projectId) {
        await dispatch(DeleteProjectService(`${VITE_API_URL}/projects/${projectId}`));
      }
    } finally {
      dispatch(CreateProjectActions.CreateDraftProjectLoading({ loading: false, continue: false }));
    }
  };
};

export const CreateProjectService = (
  url: string,
  id: number,
  projectData: Record<string, any>,
  project_admins: { projectAdminToRemove: string[]; projectAdminToAssign: string[] },
  file: { taskSplitGeojsonFile: File; dataExtractGeojsonFile: File; xlsFormFile: File },
  combinedFeaturesCount: number,
  isEmptyDataExtract: boolean,
  navigate: NavigateFunction,
) => {
  return async (dispatch: AppDispatch) => {
    try {
      dispatch(CreateProjectActions.CreateProjectLoading(true));

      // 1. patch project details
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

      // 5. assign & remove project managers
      const addAdminPromises = project_admins.projectAdminToAssign?.map(async (sub: any) => {
        await dispatch(
          AssignProjectManager(`${VITE_API_URL}/projects/add-manager`, {
            sub,
            project_id: id as number,
          }),
        );
      });
      const removeAdminPromises = project_admins.projectAdminToRemove?.map(async (sub: any) => {
        await dispatch(UnassignUserFromProject(`${VITE_API_URL}/projects/${id}/users/${sub}`));
      });
      await Promise.all([addAdminPromises, removeAdminPromises]);

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

      // revert project status to draft if any error arises during project generation
      await API.patch(url, {
        status: 'DRAFT',
      });
    } finally {
      dispatch(CreateProjectActions.CreateProjectLoading(false));
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
    dispatch(CreateProjectActions.GenerateProjectFilesLoading(true));
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

      return true; // ✅ Return success
    } catch (error: any) {
      dispatch(
        CommonActions.SetSnackBar({
          message: JSON.stringify(error?.response?.data?.detail),
        }),
      );
      return false; // ❌ Return failure
    } finally {
      dispatch(CreateProjectActions.GenerateProjectFilesLoading(false));
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
    dispatch(CreateProjectActions.GetTaskSplittingPreviewLoading(true));

    const getTaskSplittingGeojson = async (url: string, projectAoiFile: any, dataExtractFile: any) => {
      try {
        const taskSplittingFileFormData = new FormData();
        taskSplittingFileFormData.append('project_geojson', projectAoiFile);
        taskSplittingFileFormData.append('no_of_buildings', no_of_buildings.toString());
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
        if (navigate) {
          navigate('/');
          dispatch(
            CommonActions.SetSnackBar({
              message: `Project deleted`,
              variant: 'success',
            }),
          );
        }
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

export const ValidateODKCredentials = (
  url: string,
  params: { odk_central_url: string; odk_central_user: string; odk_central_password: string },
) => {
  return async (dispatch: AppDispatch) => {
    const validateCustomForm = async () => {
      try {
        dispatch(CreateProjectActions.SetODKCredentialsValidating(true));
        await axios.post(url, {}, { params });
        dispatch(CreateProjectActions.SetODKCredentialsValid(true));
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: error?.response?.data?.detail || 'Failed to validate ODK Credentials',
          }),
        );
        dispatch(CreateProjectActions.SetODKCredentialsValid(false));
      } finally {
        dispatch(CreateProjectActions.SetODKCredentialsValidating(false));
      }
    };

    await validateCustomForm();
  };
};

export {
  UploadTaskAreasService,
  FormCategoryService,
  GenerateProjectFilesService,
  OrganisationService,
  GetDividedTaskFromGeojson,
  TaskSplittingPreviewService,
  GetIndividualProjectDetails,
  PatchProjectDetails,
  PostFormUpdate,
  ValidateCustomForm,
  DeleteProjectService,
};
