import React from 'react';
import CoreModules from '../../shared/CoreModules';
import IconButtonCard from '../../utilities/IconButtonCard';
import AssetModules from '../../shared/AssetModules';

const ProjectCard = () => {
  return (
    <CoreModules.Card minWidth={300} direction={'column'} spacing={1} sx={{ width: '320px', p: 2 }}>
      <CoreModules.Stack direction={'row'} spacing={2}>
        <CoreModules.Typography variant="h2">#12345</CoreModules.Typography>
        <AssetModules.RectangleIcon
        // style={{
        //   color: `${
        //     defaultTheme.palette.mapFeatureColors[
        //       history.status.toLowerCase()
        //     ]
        //   }`,
        // }}
        />
      </CoreModules.Stack>

      <CoreModules.Divider color="lightgray" />

      <CoreModules.Stack minHeight={120} direction={'column'} spacing={2}>
        <CoreModules.Typography variant="h2" style={{ wordWrap: 'break-word' }}>
          Status changed from READY to LOCKED_FOR_MAPPING by: shushila
        </CoreModules.Typography>
        <CoreModules.Stack direction={'row-reverse'}>
          <IconButtonCard
            element={
              <CoreModules.IconButton color="info" aria-label="share qrcode">
                <AssetModules.LinkIcon
                  color="info"
                  // sx={{
                  //   fontSize: defaultTheme.typography.fontSize,
                  // }}
                />
              </CoreModules.IconButton>
            }
          />
        </CoreModules.Stack>
      </CoreModules.Stack>

      <CoreModules.Divider color="lightgray" />

      <CoreModules.Stack direction={'row'} spacing={2}>
        <AssetModules.AccessTimeFilledIcon />
        <CoreModules.Typography variant="h2">date</CoreModules.Typography>
      </CoreModules.Stack>
    </CoreModules.Card>
  );
};

export default ProjectCard;
