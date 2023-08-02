import { ProjectActions } from "fmtm/ProjectSlice";
import CoreModules from "fmtm/CoreModules";
export const ProjectById = (url, existingProjectList) => {
  return async (dispatch) => {
    // dispatch(HomeActions.HomeProjectLoading(true))
    const fetchProjectById = async (url, existingProjectList) => {
      try {
        const project = await CoreModules.axios.get(url);
        const resp = project.data;
        console.log("loading :", project.data);
        const persistingValues = resp.project_tasks.map((data) => {
          return {
            id: data.id,
            project_task_name: data.project_task_name,
            task_status_str: data.task_status_str,
            outline_geojson: data.outline_geojson,
            outline_centroid: data.outline_centroid,
            task_history: data.task_history,
            locked_by_uid:data.locked_by_uid,
            locked_by_username:data.locked_by_username,
          };
        });

        // console.log("loading :", persistingValues);
        dispatch(
          ProjectActions.SetProjectTaskBoundries([
            { id: resp.id, taskBoundries: persistingValues },
          ])
        );
        dispatch(
          ProjectActions.SetProjectInfo({id:resp.id,
            outline_geojson: resp.outline_geojson,
            priority:resp.priority || 2,
            priority_str:resp.priority_str || "MEDIUM",
            title:resp.project_info?.[0]?.name,
            location_str:resp.location_str,
            description:resp.description,
            num_contributors:resp.num_contributors,
            total_tasks:resp.total_tasks,
            tasks_mapped:resp.tasks_mapped,
            tasks_validated:resp.tasks_validated,
            xform_title:resp.xform_title,
            tasks_bad:resp.tasks_bad})
        );
      } catch (error) {
        // console.log('error :', error)
      }
    };

    await fetchProjectById(url, existingProjectList);
    dispatch(ProjectActions.SetNewProjectTrigger());
  };
};

export const DownloadProjectForm = (url,payload) => {

  return async (dispatch) => {
      dispatch(ProjectActions.SetDownloadProjectFormLoading({type:payload,loading:true}))

      const fetchProjectForm = async (url,payload) => {
          try {
            let response;
            if(payload=== 'form'){
              response = await CoreModules.axios.get(url,{responseType : 'blob'});
            }else{
              response = await CoreModules.axios.get(url, {
                responseType : 'blob',
              });
            }
              var a = document.createElement("a");
              a.href = window.URL.createObjectURL(response.data);
              a.download=`Project_form.${payload=== 'form'? '.xls':'.geojson'}`;
              a.click();
              dispatch(ProjectActions.SetDownloadProjectFormLoading({type:payload,loading:false}))
            } catch (error) {
              dispatch(ProjectActions.SetDownloadProjectFormLoading({type:payload,loading:false}))
            } finally{
              dispatch(ProjectActions.SetDownloadProjectFormLoading({type:payload,loading:false}))
          }
      }
      await fetchProjectForm(url,payload);
  }
}