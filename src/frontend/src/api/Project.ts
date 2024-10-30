import { ProjectActions } from '@/store/slices/ProjectSlice';
import { CommonActions } from '@/store/slices/CommonSlice';
import CoreModules from '@/shared/CoreModules';
import { task_state, task_event } from '@/types/enums';
import { writeBinaryToOPFS } from '@/api/Files';
import { projectInfoType } from '@/models/project/projectModel';

export const ProjectById = (projectId: string) => {
  return async (dispatch) => {
    const fetchProjectById = async (projectId: string) => {
      try {
        dispatch(ProjectActions.SetProjectDetialsLoading(true));
        const project = await CoreModules.axios.get(
          `${import.meta.env.VITE_API_URL}/projects/${projectId}?project_id=${projectId}`,
        );
        const projectResp: Record<string, any> = project.data;
        const persistingValues: Record<string, any> = projectResp.tasks.map((data) => {
          return {
            id: data.id,
            index: data.project_task_index,
            outline: data.outline,
            task_state: task_state[data.task_state],
            actioned_by_uid: data.actioned_by_uid,
            actioned_by_username: data.actioned_by_username,
            task_history: data.task_history,
          };
        });
        // At top level id project id to object
        const projectTaskBoundries = [{ id: projectResp.id, taskBoundries: persistingValues }];
        dispatch(ProjectActions.SetProjectTaskBoundries([{ ...projectTaskBoundries[0] }]));
        dispatch(
          ProjectActions.SetProjectInfo({
            id: projectResp.id,
            outline: projectResp.outline,
            priority: projectResp.priority || 2,
            name: projectResp.name,
            location_str: projectResp.location_str,
            description: projectResp.description,
            short_description: projectResp.short_description,
            num_contributors: projectResp.num_contributors,
            total_tasks: projectResp.total_tasks,
            tasks_mapped: projectResp.tasks_mapped,
            tasks_validated: projectResp.tasks_validated,
            xform_category: projectResp.xform_category,
            odk_form_id: projectResp?.odk_form_id,
            tasks_bad: projectResp.tasks_bad,
            data_extract_url: projectResp.data_extract_url,
            instructions: projectResp?.per_task_instructions,
            odk_token: projectResp?.odk_token,
            custom_tms_url: projectResp?.custom_tms_url,
            organisation_id: projectResp?.organisation_id,
            organisation_logo: projectResp?.organisation_logo,
            created_at: projectResp?.created_at,
          }),
        );
        dispatch(ProjectActions.SetProjectDetialsLoading(false));
      } catch (error) {
        if (error.response.status === 404) {
          dispatch(CommonActions.SetProjectNotFound(true));
        }
        dispatch(ProjectActions.SetProjectDetialsLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Failed to fetch project.',
            variant: 'error',
            duration: 2000,
          }),
        );
      }
    };

    await fetchProjectById(projectId);
    dispatch(ProjectActions.SetNewProjectTrigger());
  };
};

export const DownloadProjectForm = (url: string, downloadType: 'form' | 'geojson', projectId: string) => {
  return async (dispatch) => {
    dispatch(ProjectActions.SetDownloadProjectFormLoading({ type: downloadType, loading: true }));

    const fetchProjectForm = async (url: string, downloadType: 'form' | 'geojson', projectId: string) => {
      try {
        let response;
        if (downloadType === 'form') {
          response = await CoreModules.axios.get(url, { responseType: 'blob' });
        } else {
          response = await CoreModules.axios.get(url, {
            responseType: 'blob',
          });
        }
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(response.data);
        a.download = `${
          downloadType === 'form' ? `project_form_${projectId}.xlsx` : `task_polygons_${projectId}.geojson`
        }`;
        a.click();
        dispatch(ProjectActions.SetDownloadProjectFormLoading({ type: downloadType, loading: false }));
      } catch (error) {
        dispatch(ProjectActions.SetDownloadProjectFormLoading({ type: downloadType, loading: false }));
      } finally {
        dispatch(ProjectActions.SetDownloadProjectFormLoading({ type: downloadType, loading: false }));
      }
    };
    await fetchProjectForm(url, downloadType, projectId);
  };
};

export const DownloadDataExtract = (url: string, projectId: string) => {
  return async (dispatch) => {
    dispatch(ProjectActions.SetDownloadDataExtractLoading(true));

    const getDownloadExtract = async (url: string, projectId: string) => {
      try {
        let response;
        response = await CoreModules.axios.get(url, {
          responseType: 'blob',
        });
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(response.data);
        a.download = `${projectId}_map_features.geojson`;
        a.click();
        dispatch(ProjectActions.SetDownloadDataExtractLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetDownloadDataExtractLoading(false));
      } finally {
        dispatch(ProjectActions.SetDownloadDataExtractLoading(false));
      }
    };
    await getDownloadExtract(url, projectId);
  };
};

export const GetTilesList = (url: string) => {
  return async (dispatch) => {
    dispatch(ProjectActions.SetTilesListLoading(true));

    const fetchTilesList = async (url: string) => {
      try {
        const response = await CoreModules.axios.get(url);
        dispatch(ProjectActions.SetTilesList(response.data));
        dispatch(ProjectActions.SetTilesListLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetTilesListLoading(false));
      } finally {
        dispatch(ProjectActions.SetTilesListLoading(false));
      }
    };
    await fetchTilesList(url);
  };
};

export const GenerateProjectTiles = (url: string, projectId: string, data: object) => {
  return async (dispatch) => {
    dispatch(ProjectActions.SetGenerateProjectTilesLoading(true));

    const generateProjectTiles = async (url: string, projectId: string) => {
      try {
        await CoreModules.axios.post(url, data);
        dispatch(GetTilesList(`${import.meta.env.VITE_API_URL}/projects/${projectId}/tiles/`));
        dispatch(ProjectActions.SetGenerateProjectTilesLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetGenerateProjectTilesLoading(false));
      } finally {
        dispatch(ProjectActions.SetGenerateProjectTilesLoading(false));
      }
    };
    await generateProjectTiles(url, projectId);
  };
};

export const DownloadTile = (url: string, payload: Partial<projectInfoType>, toOpfs: boolean = false) => {
  return async (dispatch) => {
    dispatch(ProjectActions.SetDownloadTileLoading({ type: payload, loading: true }));

    const getDownloadTile = async (url: string, payload: Partial<projectInfoType>, toOpfs: boolean) => {
      try {
        const response = await CoreModules.axios.get(url, {
          responseType: 'arraybuffer',
        });

        // Get filename from Content-Disposition header
        const tileData = response.data;

        if (toOpfs) {
          // Copy to OPFS filesystem for offline use
          const projectId = payload.id;
          const filePath = `${projectId}/all.pmtiles`;
          await writeBinaryToOPFS(filePath, tileData);
          // Set the OPFS file path to project state
          dispatch(ProjectActions.SetProjectOpfsBasemapPath(filePath));
          return;
        }

        const filename = response.headers['content-disposition'].split('filename=')[1];
        console.log(filename);
        // Create Blob from ArrayBuffer
        const blob = new Blob([tileData], { type: response.headers['content-type'] });
        const downloadUrl = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        a.click();

        // Clean up object URL
        URL.revokeObjectURL(downloadUrl);

        dispatch(ProjectActions.SetDownloadTileLoading({ type: payload, loading: false }));
      } catch (error) {
        dispatch(ProjectActions.SetDownloadTileLoading({ type: payload, loading: false }));
      } finally {
        dispatch(ProjectActions.SetDownloadTileLoading({ type: payload, loading: false }));
      }
    };
    await getDownloadTile(url, payload, toOpfs);
  };
};

export const GetSubmissionDashboard = (url: string) => {
  return async (dispatch) => {
    const GetSubmissionDashboard = async (url: string) => {
      try {
        dispatch(ProjectActions.SetProjectDashboardLoading(true));
        const response = await CoreModules.axios.get(url);
        dispatch(ProjectActions.SetProjectDashboardDetail(response.data));
        dispatch(ProjectActions.SetProjectDashboardLoading(false));
      } catch (error) {
        if (error.response.status === 404) {
          dispatch(CommonActions.SetProjectNotFound(true));
        }
        dispatch(ProjectActions.SetProjectDashboardLoading(false));
      } finally {
        dispatch(ProjectActions.SetProjectDashboardLoading(false));
      }
    };
    await GetSubmissionDashboard(url);
  };
};

export const GetEntityInfo = (url: string) => {
  return async (dispatch) => {
    const getEntityOsmMap = async (url: string) => {
      try {
        dispatch(ProjectActions.SetEntityToOsmIdMappingLoading(true));
        dispatch(CoreModules.TaskActions.SetTaskSubmissionStatesLoading(true));
        const response = await CoreModules.axios.get(url);
        dispatch(ProjectActions.SetEntityToOsmIdMapping(response.data));
        dispatch(CoreModules.TaskActions.SetTaskSubmissionStates(response.data));
        dispatch(ProjectActions.SetEntityToOsmIdMappingLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetEntityToOsmIdMappingLoading(false));
        dispatch(CoreModules.TaskActions.SetTaskSubmissionStatesLoading(false));
      } finally {
        dispatch(ProjectActions.SetEntityToOsmIdMappingLoading(false));
        dispatch(CoreModules.TaskActions.SetTaskSubmissionStatesLoading(false));
      }
    };
    await getEntityOsmMap(url);
  };
};

export const GetProjectComments = (url: string) => {
  return async (dispatch) => {
    const getProjectComments = async (url: string) => {
      try {
        dispatch(ProjectActions.SetProjectGetCommentsLoading(true));
        const response = await CoreModules.axios.get(url);
        dispatch(ProjectActions.SetProjectCommentsList(response.data));
        dispatch(ProjectActions.SetProjectGetCommentsLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetProjectGetCommentsLoading(false));
      } finally {
        dispatch(ProjectActions.SetProjectGetCommentsLoading(false));
      }
    };
    await getProjectComments(url);
  };
};

export const PostProjectComments = (
  url: string,
  payload: { event: task_event.COMMENT; task_id: number; comment: string },
) => {
  return async (dispatch) => {
    const postProjectComments = async (url: string) => {
      try {
        dispatch(ProjectActions.SetPostProjectCommentsLoading(true));
        if (!('event' in payload)) {
          payload = { event: task_event.COMMENT, ...payload };
        }
        const response = await CoreModules.axios.post(url, payload);
        dispatch(ProjectActions.UpdateProjectCommentsList(response.data));
        dispatch(ProjectActions.SetPostProjectCommentsLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetPostProjectCommentsLoading(false));
      } finally {
        dispatch(ProjectActions.SetPostProjectCommentsLoading(false));
      }
    };
    await postProjectComments(url);
  };
};

export const GetProjectTaskActivity = (url: string) => {
  return async (dispatch) => {
    const getProjectActivity = async (url: string) => {
      try {
        dispatch(ProjectActions.SetProjectTaskActivityLoading(true));
        const response = await CoreModules.axios.get(url);
        dispatch(ProjectActions.SetProjectTaskActivity(response.data));
        dispatch(ProjectActions.SetProjectTaskActivityLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetProjectTaskActivityLoading(false));
      } finally {
        dispatch(ProjectActions.SetProjectTaskActivityLoading(false));
      }
    };
    await getProjectActivity(url);
  };
};

export const UpdateEntityState = (url: string, payload: { entity_id: string; status: number; label: string }) => {
  return async (dispatch) => {
    const updateEntityState = async (url: string, payload: { entity_id: string; status: number; label: string }) => {
      try {
        dispatch(ProjectActions.UpdateEntityStateLoading(true));
        const response = await CoreModules.axios.post(url, payload);
        dispatch(ProjectActions.UpdateEntityState(response.data));
        dispatch(ProjectActions.UpdateEntityStateLoading(false));
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: error?.response?.data?.detail || 'Failed to update entity state.',
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(ProjectActions.UpdateEntityStateLoading(false));
      }
    };
    await updateEntityState(url, payload);
  };
};

export const DownloadSubmissionGeojson = (url: string, projectName: string) => {
  return async (dispatch) => {
    dispatch(ProjectActions.SetDownloadSubmissionGeojsonLoading(true));

    const downloadSubmissionGeojson = async (url: string) => {
      try {
        const response = await CoreModules.axios.get(url, { responseType: 'blob' });
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(response.data);
        a.download = `${projectName}.geojson`;
        a.click();
        dispatch(ProjectActions.SetDownloadSubmissionGeojsonLoading(false));
      } catch (error) {
        const errortxt = JSON.parse(await error.response.data.text()).detail;
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: errortxt || 'Failed to download submission geojson.',
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(ProjectActions.SetDownloadSubmissionGeojsonLoading(false));
      } finally {
        dispatch(ProjectActions.SetDownloadSubmissionGeojsonLoading(false));
      }
    };
    await downloadSubmissionGeojson(url);
  };
};
