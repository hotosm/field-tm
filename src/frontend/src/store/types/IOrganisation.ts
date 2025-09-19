import { consentDetailsFormDataType, OrganizationAdminsModel } from '@/models/organisation/organisationModel';

export interface IOrganisationState {
  consentDetailsFormData: consentDetailsFormDataType;
  consentApproval: boolean;
  organizationDeleteLoading: boolean;
  getOrganizationAdminsLoading: boolean;
  organizationAdmins: OrganizationAdminsModel[];
  addOrganizationAdminPending: boolean;
}
