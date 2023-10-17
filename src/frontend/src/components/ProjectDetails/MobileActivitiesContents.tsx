import React from 'react';
import ActivitiesPanel from '../ActivitiesPanel';
import CoreModules from '../../shared/CoreModules';

const MobileActivitiesContents = ({ map, mainView, mapDivPostion }) => {
  const params = CoreModules.useParams();
  const state = CoreModules.useAppSelector((state) => state.project);
  const defaultTheme = CoreModules.useAppSelector((state) => state.theme.hotTheme);

  return (
    <div className="fmtm-w-full fmtm-bg-white fmtm-mb-[12vh]">
      <CoreModules.Stack sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center' }}>
        <ActivitiesPanel
          params={params}
          state={state.projectTaskBoundries}
          defaultTheme={defaultTheme}
          map={map}
          view={mainView}
          mapDivPostion={mapDivPostion}
          states={state}
        />
      </CoreModules.Stack>
    </div>
  );
};

export default MobileActivitiesContents;
