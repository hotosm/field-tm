import axios from 'axios';
import { CreateProjectActions } from '../store/slices/CreateProjectSlice';
import { CreateProjectDetailsModel, FormCategoryListModel } from '../models/createproject/createProjectModel';
import enviroment from "../environment";


const CreateProjectService: Function = (url: string,payload: any,fileUpload: any) => {

    return async (dispatch) => {
        dispatch(CreateProjectActions.CreateProjectLoading(true))

        const postCreateProjectDetails = async (url,payload,fileUpload) => {

            try {
                const postNewProjectDetails = await axios.post(url,payload)
                const resp: CreateProjectDetailsModel = postNewProjectDetails.data;
                if(payload.splitting_algorithm === 'Custom Multipolygon'){
                    dispatch(UploadAreaService(`${enviroment.baseApiUrl}/projects/${resp.id}/upload_multi_polygon`,fileUpload));
                }
                dispatch(UploadAreaService(`${enviroment.baseApiUrl}/projects/${resp.id}/upload`,fileUpload));
                dispatch(CreateProjectActions.PostProjectDetails(resp));

            } catch (error) {
                console.log(error,'error');
                dispatch(CreateProjectActions.CreateProjectLoading(false));
            }
        }

        await postCreateProjectDetails(url,payload,fileUpload);

    }

}
const FormCategoryService: Function = (url: string) => {

    return async (dispatch) => {
        dispatch(CreateProjectActions.GetFormCategoryLoading(true))

        const getFormCategoryList = async (url) => {

            try {
                const getFormCategoryListResponse = await axios.get(url)
                const resp: FormCategoryListModel = getFormCategoryListResponse.data;
                dispatch(CreateProjectActions.GetFormCategoryList(resp));

            } catch (error) {
                dispatch(CreateProjectActions.GetFormCategoryListLoading(false));
            }
        }

        await getFormCategoryList(url);

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

export {UploadAreaService,CreateProjectService,FormCategoryService}