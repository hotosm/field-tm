import { homeProjectPaginationTypes, projectType, snackbarTypes } from '@/models/home/homeModel';

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
