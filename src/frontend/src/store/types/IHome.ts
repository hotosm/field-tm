import { projectType } from '@/models/home/homeModel';
import { paginationType } from '@/store/types/ICommon';

export type HomeStateTypes = {
  homeProjectSummary: projectType[];
  selectedProject: projectType | {};
  homeProjectLoading: boolean;
  showMapStatus: boolean;
  homeProjectPagination: paginationType;
};
