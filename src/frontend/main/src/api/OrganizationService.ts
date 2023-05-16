import axios from 'axios';
import { HomeProjectCardModel } from '../models/home/homeModel';
import { OrganizationDataModel, OrganizationModal } from '../models/organization/organizationModel';
import { CommonActions } from '../store/slices/CommonSlice';
import { OrganizationAction } from '../store/slices/organizationSlice';

function appendObjectToFormData(formData, object) {
    for (const [key, value] of Object.entries(object)) {
        if(key === 'logo'){
            formData.append(key,value[0])
        }
      formData.append(key, value);
    }
  }
export const OrganizationService: Function = (url: string,payload:OrganizationModal) => {

    return async (dispatch) => {
        dispatch(CommonActions.PostOrganizationLoading(true))

        const postOrganization = async (url,payload) => {

            try {
                const generateApiFormData = new FormData();
               
                // generateApiFormData.append('upload',payload.logo[0]);
                appendObjectToFormData(generateApiFormData,payload);
                const postOrganizationData = await axios.post(url,{organization:payload,generateApiFormData},
                    { 
                        headers: {
                            "Content-Type": "multipart/form-data",
                        }
                    });
                const resp: HomeProjectCardModel = postOrganizationData.data;
                // dispatch(CommonActions.SetOrganizationDetail(resp))
                dispatch(CommonActions.PostOrganizationLoading(false))
            } catch (error) {
                dispatch(CommonActions.PostOrganizationLoading(false))
            }
        }

        await postOrganization(url,payload);

    }

}

export const OrganizationDataService : Function = (url : string) => {
    return async (dispatch) => {
        dispatch(OrganizationAction.GetOrganizationDataLoading(true))
        const getOrganizationData = async (url) => {
            try {
                const getOrganizationDataResponse = await axios.get(url);
                const response : OrganizationDataModel = getOrganizationDataResponse.data;
                dispatch(OrganizationAction.GetOrganizationsData(response))
            } catch(error) {
                dispatch(OrganizationAction.GetOrganizationDataLoading(false))
            }
        }
        await getOrganizationData(url);
    }
}