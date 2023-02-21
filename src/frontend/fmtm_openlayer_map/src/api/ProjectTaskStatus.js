import axios from "axios";
import { ProjectActions } from "../store/slices/ProjectSlice";

const UpdateTaskStatus = (url,style,existingData,feature,body) => {

    return async (dispatch) => {

        const updateTask = async (url, feature,body) => {
            try {
                const response = await axios.post(url,body);

                const findIndexForUpdation = existingData.project_tasks.findIndex(obj => obj.id == response.data.id)
                let project_tasks = [...existingData.project_tasks]
                project_tasks[findIndexForUpdation] = response.data

                const updatedProject = {...existingData}
                updatedProject.project_tasks = project_tasks
                // console.log('check similarities ',updatedProject)
                dispatch(ProjectActions.SetProject(updatedProject))
                
             
            } catch (error) {
                // console.log('error ',error)
            }

        }
        await updateTask(url,feature,body)
        feature.setStyle(style)
    }
}

export default UpdateTaskStatus;