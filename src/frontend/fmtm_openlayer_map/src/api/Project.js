import axios from "axios"
import { ProjectActions } from "../store/slices/ProjectSlice"

export const ProjectById = (url) => {

    return async (dispatch) => {
        // dispatch(HomeActions.HomeProjectLoading(true))

        const fetchProjectById = async (url) => {

            try {
                // console.log('loading')
                const project = await axios.get(url)
                const resp = project.data;               
                dispatch(ProjectActions.SetProject(resp))
           
            } catch (error) {
                // console.log('error :',error)
            }
        }

       await fetchProjectById(url);

    }

}