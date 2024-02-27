export type submissionInfographicsTypes = {
  date: string;
  count: 1;
};

export type submissionContributorsTypes = {
  user: string;
  contributions: number;
};

export type submissionFormFieldsTypes = {
  path: string;
  name: string;
  type: string;
  binary: any;
  selectMultiple: any;
};

export type validatedVsMappedInfographicsTypes = {
  date: string;
  validated: number;
  mapped: number;
};

export type taskDataTypes = {
  feature_count: number;
  submission_count: number;
  task_count: number;
};
