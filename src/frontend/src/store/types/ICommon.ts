export type CommonStateTypes = {
  snackbar: snackbarTypes;
  loading: boolean;
  postOrganisationLoading: boolean;
  currentStepFormStep: {
    create_project: {
      step: number;
    };
  };
};

type snackbarTypes = {
  open: boolean;
  message: string;
  variant: 'info' | 'success' | 'error' | 'warning';
  duration: number;
};
