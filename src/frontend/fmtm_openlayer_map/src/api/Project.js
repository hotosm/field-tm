import axios from "axios"
import { ProjectActions } from "../store/slices/ProjectSlice"

export const ProjectById = (url, existingProjectList) => {

    return async (dispatch) => {
        // dispatch(HomeActions.HomeProjectLoading(true))
        const fetchProjectById = async (url, existingProjectList) => {

            try {
                // console.log('loading :')
                const project = await axios.get(url)
                const resp = project.data;

                const persistingValues = resp.project_tasks.map((data) => {
                    return {
                        id: data.id,
                        project_task_name: data.project_task_name,
                        task_status_str: data.task_status_str,
                        outline_geojson: data.outline_geojson,
                        outline_centroid: data.outline_centroid,
                        task_history: data.task_history
                    }
                })
                if (existingProjectList.length < 5) {
                    dispatch(ProjectActions.SetProjectTaskBoundries([...existingProjectList, { id: resp.id, taskBoundries: persistingValues }]))

                } else {
                    const writableExisting = [...existingProjectList];
                    writableExisting.shift()
                    dispatch(ProjectActions.SetProjectTaskBoundries([...writableExisting, { id: resp.id, taskBoundries: persistingValues }]))
                }


            } catch (error) {
                // console.log('error :', error)
            }
        }

        await fetchProjectById(url, existingProjectList);
        dispatch(ProjectActions.SetNewProjectTrigger())

    }

}