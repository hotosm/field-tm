import React from 'react';
import { useParams } from 'react-router-dom';
import TaskActivity from '@/components/ProjectDetails/Tabs/TaskActivity';
import { useAppSelector } from '@/types/reduxTypes';

type mobileActivitiesContentsType = {
  map: any;
};

const MobileActivitiesContents = ({ map }: mobileActivitiesContentsType) => {
  const params: Record<string, any> = useParams();
  const state = useAppSelector((state) => state.project);
  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);

  return (
    <div className="fmtm-w-full fmtm-bg-white fmtm-mb-[10vh]">
      <TaskActivity params={params} state={state.projectTaskBoundries} defaultTheme={defaultTheme} map={map} />
    </div>
  );
};

export default MobileActivitiesContents;
