import { consentDetailsFormDataType, GetOrganisationDataModel } from '@/models/organisation/organisationModel';

export interface IOrganisationState {
  organisationFormData: Record<string, any>;
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
}
