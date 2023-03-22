import axios from 'axios';
import { CreateProjectActions } from '../store/slices/CreateProjectSlice';
import { CreateProjectDetailsModel } from '../models/createproject/createProjectModel';


const CreateProjectService: Function = (url: string,payload: any) => {

    return async (dispatch) => {
        dispatch(CreateProjectActions.CreateProjectLoading(true))

        const postCreateProjectDetails = async (url,payload) => {

            try {
                const postNewProjectDetails = await axios.post(url,payload)
                const resp: CreateProjectDetailsModel = postNewProjectDetails.data;
                dispatch(CreateProjectActions.PostProjectDetails(resp));

            } catch (error) {
          
                dispatch(CreateProjectActions.CreateProjectLoading(false));
            }
        }

        await postCreateProjectDetails(url,payload);

    }

}
const UploadAreaService: Function = (url: string,payload: any) => {

    return async (dispatch) => {
        dispatch(CreateProjectActions.UploadAreaLoading(true))

        const postUploadArea = async (url,payload) => {

            try {
                const areaFormData = new FormData();
                areaFormData.append('upload',payload[0]);
                const postNewProjectDetails = await axios.post(url,areaFormData,
                    { 
                        headers: {
                            "Content-Type": "multipart/form-data",
                        }
                    });
                // const resp: UploadAreaDetailsModel = postNewProjectDetails.data;
                await dispatch(CreateProjectActions.UploadAreaLoading(false))
                await dispatch(CreateProjectActions.PostUploadAreaSuccess(postNewProjectDetails.data))
            } catch (error) {
                dispatch(CreateProjectActions.UploadAreaLoading(false))
            }
        }

        await postUploadArea(url,payload);

    }

}

export {UploadAreaService,CreateProjectService}