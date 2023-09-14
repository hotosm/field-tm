import React from 'react';
import IconButtonCard from '../utilities/IconButtonCard';
import environment from '../environment';
import { easeIn, easeOut } from 'ol/easing';
import CoreModules from '../shared/CoreModules';
import AssetModules from '../shared/AssetModules';
//Activity Model to be display in Activities panel
const Activities = ({ history, defaultTheme, mapDivPostion, map, view, state, params }) => {
  const index = state.projectTaskBoundries.findIndex((project) => project.id == environment.decode(params.id));

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
        <CoreModules.Stack direction={'row-reverse'}>
          <IconButtonCard
            element={
              <CoreModules.IconButton
                onClick={async () => {
                  const main = document.getElementsByClassName('mainview')[0];
                  await main.scrollTo({
                    top: mapDivPostion,
                  });

                  const centroid = state.projectTaskBoundries[index].taskBoundries.filter((task) => {
                    return task.id == history.taskId;
                  })[0].outline_centroid.geometry.coordinates;

                  map.getView().setCenter(centroid);

                  setTimeout(() => {
                    view.animate({ zoom: 19, easing: easeOut, duration: 2000 });
                  }, 100);
                }}
                color="info"
                aria-label="share qrcode"
              >
                <AssetModules.LinkIcon color="info" sx={{ fontSize: defaultTheme.typography.fontSize }} />
              </CoreModules.IconButton>
            }
          />
        </CoreModules.Stack>
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
