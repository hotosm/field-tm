import axios, { AxiosResponse } from 'axios';
import { GetOrganisationDataModel, OrganizationAdminsModel } from '@/models/organisation/organisationModel';
import { CommonActions } from '@/store/slices/CommonSlice';
import { OrganisationAction } from '@/store/slices/organisationSlice';
import { AppDispatch } from '@/store/Store';
import { NavigateFunction } from 'react-router-dom';

const VITE_API_URL = import.meta.env.VITE_API_URL;

function appendObjectToFormData(formData: FormData, object: Record<string, any>) {
  for (const [key, value] of Object.entries(object)) {
    // if (key === 'logo') {
    //     formData.append(key, value[0])
    // }
    formData.append(key, value);
  }
}

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
        dispatch(OrganisationAction.SetIndividualOrganizationLoading(true));
        const getOrganisationDataResponse = await axios.get(url);
        const response: GetOrganisationDataModel = getOrganisationDataResponse.data;
        dispatch(OrganisationAction.SetIndividualOrganization(response));
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: error.response.data.detail || 'Failed to fetch organization.',
          }),
        );
      } finally {
        dispatch(OrganisationAction.SetIndividualOrganizationLoading(false));
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

export const ApproveOrganizationService = (
  url: string,
  params: { org_id: number; set_primary_org_odk_server: boolean },
) => {
  return async (dispatch: AppDispatch) => {
    const approveOrganization = async (url: string) => {
      try {
        dispatch(OrganisationAction.SetOrganizationApproving(true));
        await axios.post(url, {}, { params });
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

export const DeleteOrganizationService = (url: string, navigate: NavigateFunction) => {
  return async (dispatch: AppDispatch) => {
    const rejectOrganization = async (url: string) => {
      try {
        dispatch(OrganisationAction.SetOrganizationDeleting(true));
        await axios.delete(url);
        navigate('/organization');
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Organization deleted successfully',
            variant: 'success',
          }),
        );
      } catch (error) {
        const message = error?.response?.data?.detail || 'Failed to delete organisation';
        dispatch(
          CommonActions.SetSnackBar({
            message,
            variant: 'error',
          }),
        );
      } finally {
        dispatch(OrganisationAction.SetOrganizationDeleting(false));
      }
    };
    await rejectOrganization(url);
  };
};

export const GetOrganizationAdminsService = (url: string, params: { org_id: number }) => {
  return async (dispatch: AppDispatch) => {
    const getOrganizationAdmins = async (url: string, params: { org_id: number }) => {
      try {
        dispatch(OrganisationAction.GetOrganizationAdminsLoading(true));
        const getOrganizationAdminsResponse: AxiosResponse<OrganizationAdminsModel[]> = await axios.get(url, {
          params,
        });
        const response = getOrganizationAdminsResponse.data;
        dispatch(OrganisationAction.SetOrganizationAdmins(response));
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: 'Failed to fetch organization admins',
          }),
        );
      } finally {
        dispatch(OrganisationAction.GetOrganizationAdminsLoading(false));
      }
    };
    await getOrganizationAdmins(url, params);
  };
};

export const AddOrganizationAdminService = (url: string, user: string[], org_id: number) => {
  return async (dispatch: AppDispatch) => {
    dispatch(OrganisationAction.SetAddOrganizationAdminPending(true));
    try {
      const addOrganizationAdmin = async (url: string, params: { user_sub: string; org_id: number }) => {
        try {
          await axios.post(
            url,
            {},
            {
              params,
            },
          );
        } catch (error) {
          dispatch(
            CommonActions.SetSnackBar({
              message: error.response.data?.detail || 'Failed to create organization admin',
            }),
          );
        }
      };

      const promises = user?.map(async (user_sub) => {
        await addOrganizationAdmin(url, { user_sub, org_id });
      });
      await Promise.all(promises);
      dispatch(GetOrganizationAdminsService(`${VITE_API_URL}/organisation/org-admins`, { org_id: +org_id }));
    } finally {
      dispatch(OrganisationAction.SetAddOrganizationAdminPending(false));
    }
  };
};

export const DeleteOrganizationAdminService = (
  url: string,
  params: { org_id: number },
  user_sub: string,
  organizationAdmins: OrganizationAdminsModel[],
) => {
  return async (dispatch: AppDispatch) => {
    const deleteOrganizationAdmins = async (url: string, params: { org_id: number }) => {
      try {
        dispatch(OrganisationAction.SetDeleteOrganizationAdminPending(true));
        await axios.delete(url, {
          params,
        });
        dispatch(
          OrganisationAction.SetOrganizationAdmins(organizationAdmins?.filter((admin) => admin.user_sub !== user_sub)),
        );
      } catch (error) {
        dispatch(
          CommonActions.SetSnackBar({
            message: error.response.data?.detail || 'Failed to delete organization admin',
          }),
        );
      } finally {
        dispatch(OrganisationAction.SetDeleteOrganizationAdminPending(false));
      }
    };
    await deleteOrganizationAdmins(url, params);
  };
};
