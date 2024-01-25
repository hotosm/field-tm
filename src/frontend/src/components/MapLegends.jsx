import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';

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
      value: 'Ready For Validation',
      color: defaultTheme.palette.mapFeatureColors.mapped,
      status: 'none',
    },
    {
      value: 'Locked For Validation',
      color: defaultTheme.palette.mapFeatureColors.locked_for_validation,
      status: 'lock',
    },
    {
      value: 'Validated',
      color: defaultTheme.palette.mapFeatureColors.validated,
      status: 'none',
    },
    // {
    //   value: 'Bad',
    //   color: defaultTheme.palette.mapFeatureColors.bad,
    //   status: 'none',
    // },
    {
      value: 'More mapping needed',
      color: defaultTheme.palette.mapFeatureColors.invalidated,
      status: 'none',
    },
    {
      value: 'Locked',
      color: defaultTheme.palette.mapFeatureColors.invalidated,
      status: 'none',
      type: 'locked',
    },
  ];

  const LegendListItem = ({ data }) => {
    return (
      <div className="fmtm-flex fmtm-items-center fmtm-gap-3">
        <div className="fmtm-border-[1px] fmtm-border-gray-200">
          {data.type !== 'locked' ? (
            <CoreModules.IconButton
              style={{ backgroundColor: data.color, borderRadius: 0 }}
              {...iconBtnProps}
              color="primary"
              component="label"
              className="fmtm-w-10 fmtm-h-10"
            ></CoreModules.IconButton>
          ) : (
            <AssetModules.LockIcon sx={{ fontSize: '40px' }} />
          )}
        </div>
        <p className="fmtm-text-lg">{data.value}</p>
      </div>
    );
  };
  return (
    // <CoreModules.Stack direction={direction} spacing={spacing}>
    //   {MapDetails.map((data, index) => {
    //     return (
    //       <CoreModules.Stack key={index} direction={'row'} spacing={1} p={1}>
    //         <CoreModules.IconButton
    //           style={{ backgroundColor: data.color, borderRadius: 0 }}
    //           {...iconBtnProps}
    //           color="primary"
    //           component="label"
    //         >
    //           <AssetModules.LockIcon style={{ color: data.status == 'none' ? data.color : 'white' }} />
    //         </CoreModules.IconButton>
    //         {valueStatus && (
    //           <CoreModules.Stack style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
    //             <CoreModules.Typography>{data.value}</CoreModules.Typography>
    //           </CoreModules.Stack>
    //         )}
    //       </CoreModules.Stack>
    //     );
    //   })}
    // </CoreModules.Stack>
    <div className="fmtm-py-0 sm:fmtm-py-3">
      <div className="sm:fmtm-hidden fmtm-flex fmtm-gap-3 fmtm-border-b-[1px] fmtm-pb-2 fmtm-mb-4">
        <AssetModules.LegendToggleIcon className=" fmtm-text-primaryRed" sx={{ fontSize: '35px' }} />
        <p className="fmtm-text-2xl">Map Legend</p>
      </div>
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-4">
        {MapDetails.map((data, index) => {
          return <LegendListItem data={data} key={index} />;
        })}
      </div>
    </div>
  );
};

export default MapLegends;
