import { ProjectActions } from '../store/slices/ProjectSlice';
import CoreModules from '../shared/CoreModules';
import environment from '../environment';
export const ProjectById = (url, existingProjectList, projectId) => {
  return async (dispatch) => {
    // dispatch(HomeActions.HomeProjectLoading(true))
    const fetchProjectById = async (url, existingProjectList) => {
      try {
        const project = await CoreModules.axios.get(url);
        const taskBbox = await CoreModules.axios.get(
          `${environment.baseApiUrl}/tasks/point_on_surface?project_id=${projectId}`,
        );
        const resp = project.data;
        const persistingValues = resp.project_tasks.map((data) => {
          return {
            id: data.id,
            project_task_name: data.project_task_name,
            task_status_str: data.task_status_str,
            outline_geojson: data.outline_geojson,
            outline_centroid: data.outline_centroid,
            task_history: data.task_history,
            locked_by_uid: data.locked_by_uid,
            locked_by_username: data.locked_by_username,
          };
        });
        // added centroid from another api to projecttaskboundries
        const projectTaskBoundries = [{ id: resp.id, taskBoundries: persistingValues }];
        const mergedBboxIntoTask = projectTaskBoundries[0].taskBoundries.map((projectTask) => {
          const filteredTaskIdCentroid = taskBbox.data.find((task) => task.id === projectTask.id).point[0];
          return {
            ...projectTask,
            bbox: filteredTaskIdCentroid,
          };
        });
        dispatch(
          ProjectActions.SetProjectTaskBoundries([{ ...projectTaskBoundries[0], taskBoundries: mergedBboxIntoTask }]),
        );
        dispatch(
          ProjectActions.SetProjectInfo({
            id: resp.id,
            outline_geojson: resp.outline_geojson,
            priority: resp.priority || 2,
            priority_str: resp.priority_str || 'MEDIUM',
            title: resp.project_info?.[0]?.name,
            location_str: resp.location_str,
            description: resp.description,
            num_contributors: resp.num_contributors,
            total_tasks: resp.total_tasks,
            tasks_mapped: resp.tasks_mapped,
            tasks_validated: resp.tasks_validated,
            xform_title: resp.xform_title,
            tasks_bad: resp.tasks_bad,
          }),
        );
      } catch (error) {
        // console.log('error :', error)
      }
    };

    await fetchProjectById(url, existingProjectList);
    dispatch(ProjectActions.SetNewProjectTrigger());
  };
};

export const DownloadProjectForm = (url, payload) => {
  return async (dispatch) => {
    dispatch(ProjectActions.SetDownloadProjectFormLoading({ type: payload, loading: true }));

    const fetchProjectForm = async (url, payload) => {
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
        a.download = `Project_form.${payload === 'form' ? '.xls' : '.geojson'}`;
        a.click();
        dispatch(ProjectActions.SetDownloadProjectFormLoading({ type: payload, loading: false }));
      } catch (error) {
        dispatch(ProjectActions.SetDownloadProjectFormLoading({ type: payload, loading: false }));
      } finally {
        dispatch(ProjectActions.SetDownloadProjectFormLoading({ type: payload, loading: false }));
      }
    };
    await fetchProjectForm(url, payload);
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
        dispatch(GetTilesList(`${environment.baseApiUrl}/projects/tiles_list/${payload}/`));
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
        var a = document.createElement('a');
        a.href = window.URL.createObjectURL(response.data);
        a.download = `${payload.title}_mbtiles.mbtiles`;
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
