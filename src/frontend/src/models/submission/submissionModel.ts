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

export type submissionTableDataTypes = {
  results: any[];
  pagination: {
    total: number | null;
    page: number | null;
    prev_num: number | null;
    next_num: number | null;
    per_page: number | null;
    pages: number | null;
  };
};

export type reviewListType = {
  id: string;
  title: string;
  className: string;
  hoverClass: string;
};
