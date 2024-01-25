import axios from 'axios';
import { HomeProjectCardModel } from '@/models/home/homeModel';
import { GetOrganisationDataModel, OrganisationModal } from '@/models/organisation/organisationModel';
import { CommonActions } from '@/store/slices/CommonSlice';
import { OrganisationAction } from '@/store/slices/organisationSlice';

function appendObjectToFormData(formData, object) {
  for (const [key, value] of Object.entries(object)) {
    // if (key === 'logo') {
    //     formData.append(key, value[0])
    // }
    formData.append(key, value);
  }
}

export const OrganisationService: Function = (url: string, payload: OrganisationModal) => {
  return async (dispatch) => {
    dispatch(CommonActions.PostOrganisationLoading(true));

    const postOrganisation = async (url, payload) => {
      try {
        const generateApiFormData = new FormData();
        appendObjectToFormData(generateApiFormData, payload);
        await axios.post(url, generateApiFormData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        // const resp: HomeProjectCardModel = postOrganisationData.data;
        // dispatch(CommonActions.SetOrganisationDetail(resp))
        dispatch(CommonActions.PostOrganisationLoading(false));
      } catch (error) {
        dispatch(CommonActions.PostOrganisationLoading(false));
      }
    };

    await postOrganisation(url, payload);
  };
};

export const OrganisationDataService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(OrganisationAction.GetOrganisationDataLoading(true));
    const getOrganisationData = async (url) => {
      try {
        const getOrganisationDataResponse = await axios.get(url, { withCredentials: 'true' });
        const response: GetOrganisationDataModel = getOrganisationDataResponse.data;
        dispatch(OrganisationAction.GetOrganisationsData(response));
      } catch (error) {
        dispatch(OrganisationAction.GetOrganisationDataLoading(false));
      }
    };
    await getOrganisationData(url);
  };
};

export const PostOrganisationDataService: Function = (url: string, payload: any) => {
  return async (dispatch) => {
    dispatch(OrganisationAction.PostOrganisationDataLoading(true));

    const postOrganisationData = async (url, payload) => {
      dispatch(OrganisationAction.SetOrganisationFormData(payload));

      try {
        const generateApiFormData = new FormData();
        appendObjectToFormData(generateApiFormData, payload);

        const postOrganisationData = await axios.post(url, payload, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        const resp: HomeProjectCardModel = postOrganisationData.data;
        dispatch(OrganisationAction.PostOrganisationDataLoading(false));
        dispatch(OrganisationAction.postOrganisationData(resp));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Organization Successfully Created.',
            variant: 'success',
            duration: 2000,
          }),
        );
      } catch (error: any) {
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: error.response.data.detail,
            variant: 'error',
            duration: 2000,
          }),
        );
        dispatch(OrganisationAction.PostOrganisationDataLoading(false));
      }
    };

    await postOrganisationData(url, payload);
  };
};
