import { projectType, snackbarTypes } from '@/models/home/homeModel';
import { paginationType } from '@/store/types/ICommon';

export type HomeStateTypes = {
  homeProjectSummary: projectType[];
  selectedProject: projectType | {};
  homeProjectLoading: boolean;
  snackbar: snackbarTypes;
  showMapStatus: boolean;
  homeProjectPagination: paginationType;
};
