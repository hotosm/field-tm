import {
  submissionContributorsTypes,
  submissionFormFieldsTypes,
  submissionInfographicsTypes,
  validatedVsMappedInfographicsTypes,
} from '@/models/submission/submissionModel';

export type SubmissionStateTypes = {
  submissionDetailsLoading: boolean;
  submissionDetails: [];
  submissionInfographics: submissionInfographicsTypes[];
  submissionInfographicsLoading: boolean;
  submissionContributors: submissionContributorsTypes[];
  submissionContributorsLoading: boolean;
  submissionFormFields: submissionFormFieldsTypes[];
  submissionTableData: [];
  submissionFormFieldsLoading: boolean;
  submissionTableDataLoading: boolean;
  submissionTableRefreshing: boolean;
  validatedVsMappedInfographics: validatedVsMappedInfographicsTypes[];
  validatedVsMappedLoading: boolean;
};
