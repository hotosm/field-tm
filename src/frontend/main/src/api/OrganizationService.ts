import axios from 'axios';
import { HomeProjectCardModel } from '../models/home/homeModel';
import { GetOrganizationDataModel, OrganizationModal } from '../models/organization/organizationModel';
import { CommonActions } from '../store/slices/CommonSlice';
import { OrganizationAction } from '../store/slices/organizationSlice';


function appendObjectToFormData(formData, object) {
    for (const [key, value] of Object.entries(object)) {
        // if (key === 'logo') {
        //     formData.append(key, value[0])
        // }
        formData.append(key, value);
    }
}

export const OrganizationService: Function = (url: string, payload: OrganizationModal) => {

    return async (dispatch) => {
        dispatch(CommonActions.PostOrganizationLoading(true))

        const postOrganization = async (url, payload) => {

            try {
                const generateApiFormData = new FormData();
                appendObjectToFormData(generateApiFormData, payload);
                await axios.post(url, generateApiFormData,
                    {
                        headers: {
                            "Content-Type": "multipart/form-data",
                        }
                    });
                // const resp: HomeProjectCardModel = postOrganizationData.data;
                // dispatch(CommonActions.SetOrganizationDetail(resp))
                dispatch(CommonActions.PostOrganizationLoading(false))
            } catch (error) {
                dispatch(CommonActions.PostOrganizationLoading(false))
            }
        }

        await postOrganization(url, payload);

    }

}

export const OrganizationDataService: Function = (url: string) => {
    return async (dispatch) => {
        dispatch(OrganizationAction.GetOrganizationDataLoading(true))
        const getOrganizationData = async (url) => {
            try {
                const getOrganizationDataResponse = await axios.get(url);
                const response: GetOrganizationDataModel = getOrganizationDataResponse.data;
                dispatch(OrganizationAction.GetOrganizationsData(response))
            } catch (error) {
                dispatch(OrganizationAction.GetOrganizationDataLoading(false))
            }
        }
        await getOrganizationData(url);
    }
}

export const PostOrganizationDataService:Function = (url: string, payload: any) => {
    return async (dispatch) => {
        dispatch(OrganizationAction.PostOrganizationDataLoading(true));

        const postOrganizationData = async (url, payload) => {
            dispatch(OrganizationAction.SetOrganizationFormData(payload))

            try {
                const generateApiFormData = new FormData();
                appendObjectToFormData(generateApiFormData, payload);

                const postOrganizationData = await axios.post(
                    url,
                    payload,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data',
                        },
                    }
                );

                const resp: HomeProjectCardModel = postOrganizationData.data;
                dispatch(OrganizationAction.PostOrganizationDataLoading(false))
                dispatch(OrganizationAction.postOrganizationData(resp))
                dispatch(
                    CommonActions.SetSnackBar({
                        open: true,
                        message: 'Organization Successfully Created.',
                        variant: "success",
                        duration: 2000,
                    })
                );
            } catch (error:any) {
                dispatch(
                    CommonActions.SetSnackBar({
                        open: true,
                        message: error.response.data.detail,
                        variant: "error",
                        duration: 2000,
                    })
                );
                dispatch(OrganizationAction.PostOrganizationDataLoading(false))

            }
        };

        await postOrganizationData(url, payload);
    };
};