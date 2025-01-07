import axios from 'axios';
import { HomeProjectCardModel } from '@/models/home/homeModel';
import { GetOrganisationDataModel, OrganisationModal } from '@/models/organisation/organisationModel';
import { CommonActions } from '@/store/slices/CommonSlice';
import { OrganisationAction } from '@/store/slices/organisationSlice';
import { API } from '.';
import { LoginActions } from '@/store/slices/LoginSlice';

function appendObjectToFormData(formData: FormData, object: Record<string, any>) {
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

    const postOrganisation = async (url: string, payload: OrganisationModal) => {
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
    const getOrganisationData = async (url: string) => {
      try {
        const getOrganisationDataResponse = await API.get(url);
        const response: GetOrganisationDataModel[] = getOrganisationDataResponse.data;
        dispatch(OrganisationAction.GetOrganisationsData(response));
        dispatch(OrganisationAction.GetOrganisationDataLoading(false));
      } catch (error) {
        dispatch(OrganisationAction.GetOrganisationDataLoading(false));
        if (error.response.status === 401) {
          dispatch(LoginActions.setLoginModalOpen(true));
        }
      }
    };
    await getOrganisationData(url);
  };
};

export const MyOrganisationDataService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(OrganisationAction.GetMyOrganisationDataLoading(true));
    const getMyOrganisationData = async (url: string) => {
      try {
        const getMyOrganisationDataResponse = await API.get(url);
        const response: GetOrganisationDataModel[] = getMyOrganisationDataResponse.data;
        dispatch(OrganisationAction.GetMyOrganisationsData(response));
        dispatch(OrganisationAction.GetMyOrganisationDataLoading(false));
      } catch (error) {
        dispatch(OrganisationAction.GetMyOrganisationDataLoading(false));
      }
    };
    await getMyOrganisationData(url);
  };
};

export const PostOrganisationDataService: Function = (url: string, payload: any) => {
  return async (dispatch) => {
    dispatch(OrganisationAction.SetOrganisationFormData({}));
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

        const resp: GetOrganisationDataModel = postOrganisationData.data;

        dispatch(OrganisationAction.PostOrganisationDataLoading(false));
        dispatch(OrganisationAction.postOrganisationData(resp));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Organization Request Submitted.',
            variant: 'success',
            duration: 2000,
          }),
        );
      } catch (error: any) {
        dispatch(OrganisationAction.PostOrganisationDataLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: error.response.data.detail || 'Failed to create organization.',
            variant: 'error',
            duration: 2000,
          }),
        );
      }
    };

    await postOrganisationData(url, payload);
  };
};

export const GetIndividualOrganizationService: Function = (url: string) => {
  return async (dispatch) => {
    dispatch(OrganisationAction.SetOrganisationFormData({}));
    const getOrganisationData = async (url: string) => {
      try {
        const getOrganisationDataResponse = await axios.get(url);
        const response: GetOrganisationDataModel = getOrganisationDataResponse.data;
        dispatch(OrganisationAction.SetIndividualOrganization(response));
      } catch (error) {}
    };
    await getOrganisationData(url);
  };
};

export const PatchOrganizationDataService: Function = (url: string, payload: any) => {
  return async (dispatch) => {
    dispatch(OrganisationAction.SetOrganisationFormData({}));
    dispatch(OrganisationAction.PostOrganisationDataLoading(true));

    const patchOrganisationData = async (url, payload) => {
      dispatch(OrganisationAction.SetOrganisationFormData(payload));

      try {
        const generateApiFormData = new FormData();
        appendObjectToFormData(generateApiFormData, payload);

        const patchOrganisationData = await axios.patch(url, payload, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        const resp: HomeProjectCardModel = patchOrganisationData.data;
        dispatch(OrganisationAction.PostOrganisationDataLoading(false));
        dispatch(OrganisationAction.postOrganisationData(resp));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Organization Updated Successfully.',
            variant: 'success',
            duration: 2000,
          }),
        );
      } catch (error: any) {
        dispatch(OrganisationAction.PostOrganisationDataLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: error.response.data.detail || 'Failed to update organization.',
            variant: 'error',
            duration: 2000,
          }),
        );
      }
    };

    await patchOrganisationData(url, payload);
  };
};

export const ApproveOrganizationService: Function = (url: string) => {
  return async (dispatch) => {
    const approveOrganization = async (url: string) => {
      try {
        dispatch(OrganisationAction.SetOrganizationApproving(true));
        await axios.post(url);
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Organization approved successfully.',
            variant: 'success',
            duration: 2000,
          }),
        );
        dispatch(OrganisationAction.SetOrganizationApproving(false));
        dispatch(OrganisationAction.SetOrganisationFormData({}));
        dispatch(OrganisationAction.SetOrganizationApprovalStatus(true));
      } catch (error) {
        dispatch(OrganisationAction.SetOrganizationApproving(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Failed to approve organization.',
            variant: 'error',
            duration: 2000,
          }),
        );
      }
    };
    await approveOrganization(url);
  };
};

export const RejectOrganizationService: Function = (url: string) => {
  return async (dispatch) => {
    const rejectOrganization = async (url: string) => {
      try {
        dispatch(OrganisationAction.SetOrganizationRejecting(true));
        await axios.delete(url);
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Organization rejected successfully.',
            variant: 'success',
            duration: 2000,
          }),
        );
        dispatch(OrganisationAction.SetOrganizationRejecting(false));
        dispatch(OrganisationAction.SetOrganisationFormData({}));
        dispatch(OrganisationAction.SetOrganizationApprovalStatus(true));
      } catch (error) {
        dispatch(OrganisationAction.SetOrganizationRejecting(false));
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Failed to reject organization.',
            variant: 'error',
            duration: 2000,
          }),
        );
      }
    };
    await rejectOrganization(url);
  };
};
