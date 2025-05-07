import {
  consentDetailsFormDataType,
  GetOrganisationDataModel,
  OrganizationAdminsModel,
} from '@/models/organisation/organisationModel';

export interface IOrganisationState {
  organisationFormData: GetOrganisationDataModel;
  organisationData: GetOrganisationDataModel[];
  myOrganisationData: GetOrganisationDataModel[];
  postOrganisationData: GetOrganisationDataModel | null;
  organisationDataLoading: boolean;
  postOrganisationDataLoading: boolean;
  myOrganisationDataLoading: boolean;
  consentDetailsFormData: consentDetailsFormDataType;
  consentApproval: boolean;
  organizationApprovalStatus: {
    isSuccess: boolean;
    organizationApproving: boolean;
    organizationRejecting: boolean;
  };
  organizationDeleteLoading: boolean;
  organisationFormDataLoading: boolean;
  getOrganizationAdminsLoading: boolean;
  organizationAdmins: OrganizationAdminsModel[];
  deleteOrganizationAdminPending: boolean;
  addOrganizationAdminPending: boolean;
}
