import { homeProjectPaginationTypes, projectType, snackbarTypes } from '@/models/home/homeModel';

export type HomeStateTypes = {
  homeProjectSummary: projectType[];
  selectedProject: projectType | {};
  homeProjectLoading: boolean;
  snackbar: snackbarTypes;
  showMapStatus: boolean;
  homeProjectPagination: homeProjectPaginationTypes;
};
