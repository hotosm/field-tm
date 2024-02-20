import { GetOrganisationDataModel } from '@/models/organisation/organisationModel';

export interface IOrganisationState {
  organisationFormData: any;
  organisationData: GetOrganisationDataModel[];
  myOrganisationData: GetOrganisationDataModel[];
  postOrganisationData: any;
  organisationDataLoading: Boolean;
  postOrganisationDataLoading: Boolean;
  myOrganisationDataLoading: false;
  consentDetailsFormData: {
    give_consent: any;
    review_documentation: any;
    log_into: any;
    participated_in: any;
  };
  consentApproval: Boolean;
  organizationApprovalStatus: {
    isSuccess: Boolean;
    organizationApproving: Boolean;
    organizationRejecting: Boolean;
  };
}
