import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';

const MapLegends = ({ iconBtnProps, defaultTheme }) => {
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
              className="fmtm-w-7 fmtm-h-7 sm:fmtm-w-10 sm:fmtm-h-10"
            ></CoreModules.IconButton>
          ) : (
            <AssetModules.LockIcon className="!fmtm-text-[28px] sm:!fmtm-text-[40px]" />
          )}
        </div>
        <p className="fmtm-text-base sm:fmtm-text-lg">{data.value}</p>
      </div>
    );
  };

  return (
    <div className="fmtm-py-3">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-2 sm:fmtm-gap-4">
        {MapDetails.map((data, index) => {
          return <LegendListItem data={data} key={index} />;
        })}
      </div>
    </div>
  );
};

export default MapLegends;
