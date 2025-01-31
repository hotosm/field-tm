export type CommonStateTypes = {
  snackbar: snackbarTypes;
  loading: boolean;
  postOrganisationLoading: boolean;
  currentStepFormStep: {
    create_project: {
      step: number;
    };
  };
  projectNotFound: boolean;
};

type snackbarTypes = {
  open: boolean;
  message: string;
  variant: 'info' | 'success' | 'error' | 'warning';
  duration: number;
};

export type paginationType = {
  has_next: boolean;
  has_prev: boolean;
  next_num: number | null;
  page: number | null;
  pages: number | null;
  prev_num: number | null;
  per_page: number;
  total: number | null;
};
