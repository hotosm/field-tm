import axios from "axios"
import { ProjectActions } from "../store/slices/ProjectSlice"

export const ProjectById = (url) => {

    return async (dispatch) => {
        // dispatch(HomeActions.HomeProjectLoading(true))
        const fetchProjectById = async (url) => {

            try {
                const project = await axios.get(url)
                const resp = project.data;
                const persistingValues = resp.project_tasks.map((data) => {
                    return {
                        id: data.id,
                        project_task_name: data.project_task_name,
                        task_status_str: data.task_status_str,
                        outline_geojson: data.outline_geojson
                    }
                })
            
            dispatch(ProjectActions.SetProject({ id: resp.id, tasks: [...persistingValues] }))
            // console.log('resp :', { id: resp.id, tasks: [...persistingValues] })
        } catch (error) {
            // console.log('error :', error)
        }
    }

    await fetchProjectById(url);

}

}