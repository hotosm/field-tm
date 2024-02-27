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

type submissionInfographicsTypes = {
  date: string;
  count: 1;
};

type submissionContributorsTypes = {
  user: string;
  contributions: number;
};

type submissionFormFieldsTypes = {
  path: string;
  name: string;
  type: string;
  binary: any;
  selectMultiple: any;
};

type validatedVsMappedInfographicsTypes = {
  date: string;
  validated: number;
  mapped: number;
};
