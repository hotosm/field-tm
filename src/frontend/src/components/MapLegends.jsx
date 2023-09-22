import React from 'react';
import CoreModules from 'fmtm/CoreModules';
import AssetModules from 'fmtm/AssetModules';

const MapLegends = ({ direction, spacing, iconBtnProps, defaultTheme, valueStatus }) => {
  const MapDetails = [
    {
      value: 'Ready',
      color: defaultTheme.palette.mapFeatureColors.ready,
      status: 'none',
    },
    {
      value: 'Locked For Mapping',
      color: defaultTheme.palette.mapFeatureColors.locked_for_mapping,
      status: 'lock',
    },
    {
      value: 'Locked For Validation',
      color: defaultTheme.palette.mapFeatureColors.locked_for_validation,
      status: 'lock',
    },
    {
      value: 'Ready For Validation',
      color: defaultTheme.palette.mapFeatureColors.mapped,
      status: 'none',
    },
    {
      value: 'Validated',
      color: defaultTheme.palette.mapFeatureColors.validated,
      status: 'none',
    },
    {
      value: 'Bad',
      color: defaultTheme.palette.mapFeatureColors.bad,
      status: 'none',
    },
    {
      value: 'More mapping needed',
      color: defaultTheme.palette.mapFeatureColors.invalidated,
      status: 'none',
    },
  ];
  return (
    <CoreModules.Stack direction={direction} spacing={spacing}>
      {MapDetails.map((data, index) => {
        return (
          <CoreModules.Stack key={index} direction={'row'} spacing={1} p={1}>
            <CoreModules.IconButton
              style={{ backgroundColor: data.color, borderRadius: 0 }}
              {...iconBtnProps}
              color="primary"
              component="label"
            >
              <AssetModules.LockIcon style={{ color: data.status == 'none' ? data.color : 'white' }} />
            </CoreModules.IconButton>
            {valueStatus && (
              <CoreModules.Stack style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <CoreModules.Typography>{data.value}</CoreModules.Typography>
              </CoreModules.Stack>
            )}
          </CoreModules.Stack>
        );
      })}
    </CoreModules.Stack>
  );
};

export default MapLegends;
