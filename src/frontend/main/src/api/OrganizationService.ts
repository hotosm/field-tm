import axios from 'axios';
import { HomeActions } from '../store/slices/HomeSlice';
import { HomeProjectCardModel } from '../models/home/homeModel';
import { OrganizationModal } from '../models/organization/organizationModal';
import { CommonActions } from '../store/slices/CommonSlice';

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
