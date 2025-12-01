export type submissionContributorsTypes = {
  user: string;
  contributions: number;
};

export type reviewListType = {
  id: string;
  title: string;
  className: string;
  hoverClass: string;
};

export type formSubmissionType = { date: string; count: number; label: string };
export type validatedMappedType = { date: string; validated: number; mapped: number; label: string };
