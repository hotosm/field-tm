import {
  submissionContributorsTypes,
  submissionFormFieldsTypes,
  submissionInfographicsTypes,
  submissionTableDataTypes,
  validatedVsMappedInfographicsTypes,
} from '@/models/submission/submissionModel';

export type SubmissionStateTypes = {
  submissionDetailsLoading: boolean;
  submissionDetails: Record<string, any> | null;
  submissionInfographics: submissionInfographicsTypes[];
  submissionInfographicsLoading: boolean;
  submissionContributors: submissionContributorsTypes[];
  submissionContributorsLoading: boolean;
  submissionFormFields: submissionFormFieldsTypes[];
  submissionTableData: submissionTableDataTypes;
  submissionFormFieldsLoading: boolean;
  submissionTableDataLoading: boolean;
  submissionTableRefreshing: boolean;
  validatedVsMappedInfographics: validatedVsMappedInfographicsTypes[];
  validatedVsMappedLoading: boolean;
  updateReviewStatusModal: updateReviewStatusModal;
};

type updateReviewStatusModal = {
  toggleModalStatus: boolean;
  submissionId: string | null;
};
