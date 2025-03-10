import React from 'react';
import ActivitiesPanel from '@/components/ProjectDetails/ActivitiesPanel';
import CoreModules from '@/shared/CoreModules';
import { useAppSelector } from '@/types/reduxTypes';

type mobileActivitiesContentsType = {
  map: any;
};

const MobileActivitiesContents = ({ map }: mobileActivitiesContentsType) => {
  const params: Record<string, any> = CoreModules.useParams();
  const state = useAppSelector((state) => state.project);
  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);

  return (
    <div className="fmtm-w-full fmtm-bg-white fmtm-mb-[10vh]">
      <ActivitiesPanel params={params} state={state.projectTaskBoundries} defaultTheme={defaultTheme} map={map} />
    </div>
  );
};

export default MobileActivitiesContents;
