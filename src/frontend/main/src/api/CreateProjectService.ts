import axios from 'axios';
import { CreateProjectActions } from '../store/slices/CreateProjectSlice';
import { CreateProjectDetailsModel, FormCategoryListModel } from '../models/createproject/createProjectModel';
import enviroment from "../environment";
import { CommonActions } from '../store/slices/CommonSlice';


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
                await dispatch(UploadAreaService(`${enviroment.baseApiUrl}/projects/${resp.id}/upload`,fileUpload));
                dispatch(
                    CommonActions.SetSnackBar({
                        open: true,
                        message: 'Project Successfully Created.',
                        variant: "success",
                        duration: 1000,
                    })
                );
                await dispatch(GenerateProjectQRService(`${enviroment.baseApiUrl}/projects/${resp.id}/generate?category=${payload.xform_title}`));
                await dispatch(CreateProjectActions.PostProjectDetails(resp));
                // Added Snackbar toast for success message 
                // END

            } catch (error) {
                console.log(error.response,'error');
                console.log(error,'error2');

                // Added Snackbar toast for error message 
                dispatch(
                    CommonActions.SetSnackBar({
                        open: true,
                        message: JSON.stringify(error?.response?.data?.detail) || 'Something went wrong.' ,
                        variant: "error",
                        duration: 2000,
                    })
                );
                //END
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
                dispatch(
                    CommonActions.SetSnackBar({
                        open: true,
                        message: JSON.stringify(error.response.data.detail),
                        variant: "error",
                        duration: 2000,
                    })
                );
                dispatch(CreateProjectActions.UploadAreaLoading(false))
            }
        }

        await postUploadArea(url,payload);

    }

}
const GenerateProjectQRService: Function = (url: string,payload: any) => {

    return async (dispatch) => {
        dispatch(CreateProjectActions.GenerateProjectQRLoading(true))

        const postUploadArea = async (url,payload) => {

            try {
                const postNewProjectDetails = await axios.post(url);
                // const resp: UploadAreaDetailsModel = postNewProjectDetails.data;
                await dispatch(CreateProjectActions.GenerateProjectQRLoading(false))
                CommonActions.SetSnackBar({
                    open: true,
                    message: 'Generating QR For Project',
                    variant: "success",
                    duration: 2000,
                })
                // await dispatch(CreateProjectActions.PostUploadAreaSuccess(postNewProjectDetails.data))
                
            } catch (error) {
                dispatch(
                    CommonActions.SetSnackBar({
                        open: true,
                        message: JSON.stringify(error.response.data.detail),
                        variant: "error",
                        duration: 2000,
                    })
                );
                dispatch(CreateProjectActions.GenerateProjectQRLoading(false))
            }
        }

        await postUploadArea(url,payload);

    }

}

export {UploadAreaService,CreateProjectService,FormCategoryService,GenerateProjectQRService}