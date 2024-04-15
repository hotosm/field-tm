import React from 'react';
import IconButtonCard from '@/utilities/IconButtonCard';
import { easeIn, easeOut } from 'ol/easing';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
//Activity Model to be display in Activities panel
const Activities = ({ history, defaultTheme, mapDivPostion, map, view, state, params }) => {
  const index = state.projectTaskBoundries.findIndex((project) => project.id == params.id);

  return (
    <CoreModules.Stack minWidth={100} direction={'column'} spacing={1}>
      <CoreModules.Stack direction={'row'} spacing={2}>
        <CoreModules.Typography variant="h2">{`Task #${history.taskId}`}</CoreModules.Typography>
        <AssetModules.RectangleIcon
          style={{
            color: `${defaultTheme.palette.mapFeatureColors[history.status.toLowerCase()]}`,
          }}
        />
      </CoreModules.Stack>

      <CoreModules.Divider color="lightgray" />

      <CoreModules.Stack minHeight={120} direction={'column'} spacing={2}>
        <CoreModules.Typography variant="h2" style={{ wordWrap: 'break-word' }}>
          {history.action_text}
        </CoreModules.Typography>
      </CoreModules.Stack>

      <CoreModules.Divider color="lightgray" />

      <CoreModules.Stack direction={'row'} spacing={2}>
        <AssetModules.AccessTimeFilledIcon />
        <CoreModules.Typography variant="h2">{history.action_date}</CoreModules.Typography>
      </CoreModules.Stack>
    </CoreModules.Stack>
  );
};
export default Activities;
