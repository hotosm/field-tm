import axios from 'axios';
import { GetOrganisationDataModel, OrganisationModal } from '@/models/organisation/organisationModel';
import { CommonActions } from '@/store/slices/CommonSlice';
import { OrganisationAction } from '@/store/slices/organisationSlice';
import { API } from '.';
import { LoginActions } from '@/store/slices/LoginSlice';
import { AppDispatch } from '@/store/Store';

function appendObjectToFormData(formData: FormData, object: Record<string, any>) {
  for (const [key, value] of Object.entries(object)) {
    // if (key === 'logo') {
    //     formData.append(key, value[0])
    // }
    formData.append(key, value);
  }
}

export const OrganisationService = (url: string, payload: OrganisationModal) => {
  return async (dispatch: AppDispatch) => {
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

export const OrganisationDataService = (url: string) => {
  return async (dispatch: AppDispatch) => {
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

export const MyOrganisationDataService = (url: string) => {
  return async (dispatch: AppDispatch) => {
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

export const PostOrganisationDataService = (url: string, payload: any) => {
  return async (dispatch: AppDispatch) => {
    dispatch(OrganisationAction.PostOrganisationDataLoading(true));

    const postOrganisationData = async (url, payload) => {
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
        dispatch(OrganisationAction.SetOrganisationFormData({}));

        dispatch(
          CommonActions.SetSnackBar({
            message: 'Organization Request Submitted.',
            variant: 'success',
          }),
        );
      } catch (error: any) {
        dispatch(OrganisationAction.PostOrganisationDataLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            message: error.response.data.detail || 'Failed to create organization.',
          }),
        );
      }
    };

    await postOrganisationData(url, payload);
  };
};

export const GetIndividualOrganizationService = (url: string) => {
  return async (dispatch: AppDispatch) => {
    dispatch(OrganisationAction.SetOrganisationFormData({}));
    const getOrganisationData = async (url: string) => {
      try {
        const getOrganisationDataResponse = await axios.get(url);
        const response: GetOrganisationDataModel = getOrganisationDataResponse.data;
        dispatch(OrganisationAction.SetIndividualOrganization(response));
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: error.response.data.detail || 'Failed to fetch organization.',
          }),
        );
      }
    };
    await getOrganisationData(url);
  };
};

export const PatchOrganizationDataService = (url: string, payload: any) => {
  return async (dispatch: AppDispatch) => {
    dispatch(OrganisationAction.PostOrganisationDataLoading(true));

    const patchOrganisationData = async (url, payload) => {
      try {
        const generateApiFormData = new FormData();
        appendObjectToFormData(generateApiFormData, payload);

        const patchOrganisationData = await axios.patch(url, payload, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        const resp: GetOrganisationDataModel = patchOrganisationData.data;
        dispatch(OrganisationAction.PostOrganisationDataLoading(false));
        dispatch(OrganisationAction.postOrganisationData(resp));
        dispatch(OrganisationAction.SetOrganisationFormData({}));
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Organization Updated Successfully.',
            variant: 'success',
          }),
        );
      } catch (error: any) {
        dispatch(OrganisationAction.PostOrganisationDataLoading(false));
        dispatch(
          CommonActions.SetSnackBar({
            message: error.response.data.detail || 'Failed to update organization.',
          }),
        );
      }
    };

    await patchOrganisationData(url, payload);
  };
};

export const ApproveOrganizationService = (url: string) => {
  return async (dispatch: AppDispatch) => {
    const approveOrganization = async (url: string) => {
      try {
        dispatch(OrganisationAction.SetOrganizationApproving(true));
        await axios.post(url);
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Organization approved successfully.',
            variant: 'success',
          }),
        );
        dispatch(OrganisationAction.SetOrganizationApproving(false));
        dispatch(OrganisationAction.SetOrganisationFormData({}));
        dispatch(OrganisationAction.SetOrganizationApprovalStatus(true));
      } catch (error) {
        dispatch(OrganisationAction.SetOrganizationApproving(false));
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Failed to approve organization.',
          }),
        );
      }
    };
    await approveOrganization(url);
  };
};

export const RejectOrganizationService = (url: string) => {
  return async (dispatch: AppDispatch) => {
    const rejectOrganization = async (url: string) => {
      try {
        dispatch(OrganisationAction.SetOrganizationRejecting(true));
        await axios.delete(url);
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Organization rejected successfully.',
            variant: 'success',
          }),
        );
        dispatch(OrganisationAction.SetOrganizationRejecting(false));
        dispatch(OrganisationAction.SetOrganisationFormData({}));
        dispatch(OrganisationAction.SetOrganizationApprovalStatus(true));
      } catch (error) {
        dispatch(OrganisationAction.SetOrganizationRejecting(false));
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Failed to reject organization.',
          }),
        );
      }
    };
    await rejectOrganization(url);
  };
};
