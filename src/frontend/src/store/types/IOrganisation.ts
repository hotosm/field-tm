import { GetOrganisationDataModel } from '@/models/organisation/organisationModel';

export interface IOrganisationState {
  organisationFormData: Record<string, any>;
  organisationData: GetOrganisationDataModel[];
  myOrganisationData: GetOrganisationDataModel[];
  postOrganisationData: Record<string, any> | null;
  organisationDataLoading: boolean;
  postOrganisationDataLoading: boolean;
  myOrganisationDataLoading: false;
  consentDetailsFormData: {
    give_consent: any;
    review_documentation: any;
    log_into: any;
    participated_in: any;
  };
  consentApproval: boolean;
  organizationApprovalStatus: {
    isSuccess: boolean;
    organizationApproving: boolean;
    organizationRejecting: boolean;
  };
}
