import { homeProjectPaginationTypes, projectType } from '@/models/home/homeModel';

export type HomeStateTypes = {
  homeProjectSummary: projectType[];
  selectedProject: projectType | {};
  homeProjectLoading: boolean;
  dialogStatus: boolean;
  snackbar: snackbarTypes;
  showMapStatus: boolean;
  projectCentroidLoading: boolean;
  homeProjectPagination: homeProjectPaginationTypes;
};

type snackbarTypes = {
  open: boolean;
  message: string;
  variant: 'info' | 'success' | 'error' | 'warning';
  duration: number;
};
