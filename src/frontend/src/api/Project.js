import { ProjectActions } from '@/store/slices/ProjectSlice';
import { CommonActions } from '@/store/slices/CommonSlice';
import CoreModules from '@/shared/CoreModules';
import { task_priority_str } from '@/types/enums';
import axios from 'axios';

export const ProjectById = (existingProjectList, projectId) => {
  return async (dispatch) => {
    const fetchProjectById = async (projectId, existingProjectList) => {
      try {
        dispatch(ProjectActions.SetProjectDetialsLoading(true));
        const project = await CoreModules.axios.get(`${import.meta.env.VITE_API_URL}/projects/${projectId}`);
        const projectResp = project.data;
        const persistingValues = projectResp.tasks.map((data) => {
          return {
            id: data.id,
            outline_geojson: data.outline_geojson,
            outline_centroid: data.outline_centroid,
            task_status: task_priority_str[data.task_status],
            locked_by_uid: data.locked_by_uid,
            locked_by_username: data.locked_by_username,
            task_history: data.task_history,
            odk_token: data.odk_token,
          };
        });
        // At top level id project id to object
        const projectTaskBoundries = [{ id: projectResp.id, taskBoundries: persistingValues }];
        dispatch(ProjectActions.SetProjectTaskBoundries([{ ...projectTaskBoundries[0] }]));
        dispatch(
          ProjectActions.SetProjectInfo({
            id: projectResp.id,
            outline_geojson: projectResp.outline_geojson,
            priority: projectResp.priority || 2,
            priority_str: projectResp.priority_str || 'MEDIUM',
            title: projectResp.project_info?.name,
            location_str: projectResp.location_str,
            description: projectResp.project_info?.description,
            short_description: projectResp.project_info?.short_description,
            num_contributors: projectResp.num_contributors,
            total_tasks: projectResp.total_tasks,
            tasks_mapped: projectResp.tasks_mapped,
            tasks_validated: projectResp.tasks_validated,
            xform_category: projectResp.xform_category,
            tasks_bad: projectResp.tasks_bad,
            data_extract_url: projectResp.data_extract_url,
            instructions: projectResp?.project_info?.per_task_instructions,
          }),
        );
        dispatch(ProjectActions.SetProjectDetialsLoading(false));
      } catch (error) {
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

    await fetchProjectById(projectId, existingProjectList);
    dispatch(ProjectActions.SetNewProjectTrigger());
  };
};

export const DownloadProjectForm = (url, payload, projectId) => {
  return async (dispatch) => {
    dispatch(ProjectActions.SetDownloadProjectFormLoading({ type: payload, loading: true }));

    const fetchProjectForm = async (url, payload, projectId) => {
      try {
        let response;
        if (payload === 'form') {
          response = await CoreModules.axios.get(url, { responseType: 'blob' });
        } else {
          response = await CoreModules.axios.get(url, {
            responseType: 'blob',
          });
        }
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(response.data);
        a.download = `${payload === 'form' ? `project_form_${projectId}.xls` : `task_polygons_${projectId}.geojson`}`;
        a.click();
        dispatch(ProjectActions.SetDownloadProjectFormLoading({ type: payload, loading: false }));
      } catch (error) {
        dispatch(ProjectActions.SetDownloadProjectFormLoading({ type: payload, loading: false }));
      } finally {
        dispatch(ProjectActions.SetDownloadProjectFormLoading({ type: payload, loading: false }));
      }
    };
    await fetchProjectForm(url, payload, projectId);
  };
};
export const DownloadDataExtract = (url, payload) => {
  return async (dispatch) => {
    dispatch(ProjectActions.SetDownloadDataExtractLoading(true));

    const getDownloadExtract = async (url, payload) => {
      try {
        let response;

        response = await CoreModules.axios.get(url, {
          responseType: 'blob',
        });
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(response.data);
        a.download = `Data_Extract.geojson`;
        a.click();
        dispatch(ProjectActions.SetDownloadDataExtractLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetDownloadDataExtractLoading(false));
      } finally {
        dispatch(ProjectActions.SetDownloadDataExtractLoading(false));
      }
    };
    await getDownloadExtract(url, payload);
  };
};
export const GetTilesList = (url) => {
  return async (dispatch) => {
    dispatch(ProjectActions.SetTilesListLoading(true));

    const fetchTilesList = async (url) => {
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
export const GenerateProjectTiles = (url, payload) => {
  return async (dispatch) => {
    dispatch(ProjectActions.SetGenerateProjectTilesLoading(true));

    const generateProjectTiles = async (url, payload) => {
      try {
        const response = await CoreModules.axios.get(url);
        dispatch(GetTilesList(`${import.meta.env.VITE_API_URL}/projects/tiles_list/${payload}/`));
        dispatch(ProjectActions.SetGenerateProjectTilesLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetGenerateProjectTilesLoading(false));
      } finally {
        dispatch(ProjectActions.SetGenerateProjectTilesLoading(false));
      }
    };
    await generateProjectTiles(url, payload);
  };
};

export const DownloadTile = (url, payload) => {
  return async (dispatch) => {
    dispatch(ProjectActions.SetDownloadTileLoading({ type: payload, loading: true }));

    const getDownloadTile = async (url, payload) => {
      try {
        const response = await CoreModules.axios.get(url, {
          responseType: 'blob',
        });

        // Get filename from content-disposition header
        const filename = response.headers['content-disposition'].split('filename=')[1];

        var a = document.createElement('a');
        a.href = window.URL.createObjectURL(response.data);
        a.download = filename;
        a.click();
        dispatch(ProjectActions.SetDownloadTileLoading({ type: payload, loading: false }));
      } catch (error) {
        dispatch(ProjectActions.SetDownloadTileLoading({ type: payload, loading: false }));
      } finally {
        dispatch(ProjectActions.SetDownloadTileLoading({ type: payload, loading: false }));
      }
    };
    await getDownloadTile(url, payload);
  };
};

export const GetProjectDashboard = (url) => {
  return async (dispatch) => {
    const getProjectDashboard = async (url) => {
      try {
        dispatch(ProjectActions.SetProjectDashboardLoading(true));
        const response = await CoreModules.axios.get(url);
        dispatch(ProjectActions.SetProjectDashboardDetail(response.data));
        dispatch(ProjectActions.SetProjectDashboardLoading(false));
      } catch (error) {
        dispatch(ProjectActions.SetProjectDashboardLoading(false));
      } finally {
        dispatch(ProjectActions.SetProjectDashboardLoading(false));
      }
    };
    await getProjectDashboard(url);
  };
};

export const GetProjectComments = (url) => {
  return async (dispatch) => {
    const getProjectComments = async (url) => {
      try {
        dispatch(ProjectActions.SetProjectGetCommentsLoading(true));
        const response = await axios.get(url);
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

export const PostProjectComments = (url, payload) => {
  return async (dispatch) => {
    const postProjectComments = async (url) => {
      try {
        dispatch(ProjectActions.SetPostProjectCommentsLoading(true));
        const response = await axios.post(url, payload);
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
