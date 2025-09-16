import axios, { AxiosResponse } from 'axios';
import { OrganizationAdminsModel } from '@/models/organisation/organisationModel';
import { CommonActions } from '@/store/slices/CommonSlice';
import { OrganisationAction } from '@/store/slices/organisationSlice';
import { AppDispatch } from '@/store/Store';
import { NavigateFunction } from 'react-router-dom';

const VITE_API_URL = import.meta.env.VITE_API_URL;

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
