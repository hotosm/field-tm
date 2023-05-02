import axios from 'axios';
import { CreateProjectActions } from '../store/slices/CreateProjectSlice';
import { CreateProjectDetailsModel, FormCategoryListModel, OrganisationListModel } from '../models/createproject/createProjectModel';
import enviroment from "../environment";
import { CommonActions } from '../store/slices/CommonSlice';


const CreateProjectService: Function = (url: string,payload: any,fileUpload: any) => {

    return async (dispatch) => {
        dispatch(CreateProjectActions.CreateProjectLoading(true))
        dispatch(CommonActions.SetLoading(true))

        const postCreateProjectDetails = async (url,payload,fileUpload) => {

            try {
                const postNewProjectDetails = await axios.post(url,payload)
                const resp: CreateProjectDetailsModel = postNewProjectDetails.data;
                await dispatch(CreateProjectActions.PostProjectDetails(resp));

                if(payload.splitting_algorithm === 'Custom Multipolygon'){
                    dispatch(UploadAreaService(`${enviroment.baseApiUrl}/projects/${resp.id}/upload_multi_polygon`,fileUpload));
                }else{

                    await dispatch(UploadAreaService(`${enviroment.baseApiUrl}/projects/${resp.id}/upload`,fileUpload));
                }
                dispatch(
                    CommonActions.SetSnackBar({
                        open: true,
                        message: 'Project Successfully Created Now Generating QR For Project',
                        variant: "success",
                        duration: 2000,
                    })
                );
                await dispatch(GenerateProjectQRService(`${enviroment.baseApiUrl}/projects/${resp.id}/generate`,payload));
                dispatch(CommonActions.SetLoading(false))


            } catch (error) {
                console.log(error.response,'error');
                console.log(error,'error2');
                dispatch(CommonActions.SetLoading(false))

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
                        message: JSON.stringify(error?.response?.data?.detail) || 'Something Went Wrong.',
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
        dispatch(CommonActions.SetLoading(true))
        
        const postUploadArea = async (url,payload) => {

            try {
                const generateApiFormData = new FormData();
                if(payload.form_ways === 'Upload a Custom Form'){
                    generateApiFormData.append('upload',payload.uploaded_form[0]);
                }else{
                    generateApiFormData.append('upload','');

                }
                const postNewProjectDetails = await axios.post(url,generateApiFormData,
                    { 
                        headers: {
                            "Content-Type": "multipart/form-data",
                        }
                    });
                const resp: string = postNewProjectDetails.data;
                await dispatch(CreateProjectActions.GenerateProjectQRLoading(false))
                dispatch(
                    CommonActions.SetSnackBar({
                    open: true,
                    message: 'QR Generation Completed.',
                    variant: "success",
                    duration: 2000,
                }));
                dispatch(CommonActions.SetLoading(false))
                await dispatch(CreateProjectActions.ClearCreateProjectFormData())
                await dispatch(CreateProjectActions.GenerateProjectQRSuccess(resp))
                
            } catch (error) {
                dispatch(CommonActions.SetLoading(false))
                dispatch(
                    CommonActions.SetSnackBar({
                        open: true,
                        message: JSON.stringify(error?.response?.data?.detail),
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

const OrganisationService: Function = (url: string) => {

    return async (dispatch) => {
        dispatch(CreateProjectActions.GetOrganisationListLoading(true))

        const getOrganisationList = async (url) => {
            try {
                const getOrganisationListResponse = await axios.get(url)
                const resp: OrganisationListModel = getOrganisationListResponse.data;
                dispatch(CreateProjectActions.GetOrganisationList(resp));

            } catch (error) {
                dispatch(CreateProjectActions.GetOrganizationListLoading(false));
            }
        }

        await getOrganisationList(url);

    }

}

const UploadCustomXLSFormService: Function = (url: string,payload: any) => {

    return async (dispatch) => {
        dispatch(CreateProjectActions.UploadCustomXLSFormLoading(true))

        const postUploadCustomXLSForm = async (url,payload) => {

            try {
                const customXLSFormData = new FormData();
                customXLSFormData.append('upload',payload[0]);
                const postCustomXLSForm = await axios.post(url,customXLSFormData,
                    { 
                        headers: {
                            "Content-Type": "multipart/form-data",
                        }
                    });
                await dispatch(CreateProjectActions.UploadCustomXLSFormLoading(false))
                await dispatch(CreateProjectActions.UploadCustomXLSFormSuccess(postCustomXLSForm.data))
                
            } catch (error) {
                dispatch(
                    CommonActions.SetSnackBar({
                        open: true,
                        message: JSON.stringify(error.response.data.detail) || "Something Went Wrong",
                        variant: "error",
                        duration: 2000,
                    })
                );
                dispatch(CreateProjectActions.UploadCustomXLSFormLoading(false))
            }
        }

        await postUploadCustomXLSForm(url,payload);

    }

}

const GenerateProjectLog: Function = (url: string,params:any) => {

    return async (dispatch) => {
        dispatch(CreateProjectActions.GenerateProjectLogLoading(true))

        const getGenerateProjectLog = async (url,params) => {
            try {
                const getGenerateProjectLogResponse = await axios.get(url,{params})
                const resp: OrganisationListModel = getGenerateProjectLogResponse.data;
                dispatch(CreateProjectActions.SetGenerateProjectLog(resp));

            } catch (error) {
                dispatch(CreateProjectActions.GenerateProjectLogLoading(false));
            }
        }

        await getGenerateProjectLog(url,params);

    }

}
export {UploadAreaService,CreateProjectService,FormCategoryService,GenerateProjectQRService,OrganisationService,UploadCustomXLSFormService,GenerateProjectLog}