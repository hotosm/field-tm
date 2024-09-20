import React from 'react';
import AssetModules from '@/shared/AssetModules';

type mapDetialsType = {
  value: string;
  color: string;
  status: string;
  type?: string;
};

const MapLegends = ({ defaultTheme }: { defaultTheme: any }) => {
  const MapDetails: mapDetialsType[] = [
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

  const LegendListItem = ({ data }: { data: mapDetialsType }) => {
    return (
      <div className="fmtm-flex fmtm-items-center fmtm-gap-3">
        {data.type !== 'locked' ? (
          <div
            style={{ backgroundColor: data.color, borderRadius: 0 }}
            color="primary"
            className="!fmtm-w-5 !fmtm-h-5 fmtm-border-[1px] fmtm-border-gray-200"
          ></div>
        ) : (
          <AssetModules.LockIcon className="!fmtm-text-[20px]" />
        )}
        <p className="fmtm-text-base fmtm-text-[#494949]">{data.value}</p>
      </div>
    );
  };

  return (
    <div className="fmtm-py-3">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
        {MapDetails.map((data, index) => {
          return <LegendListItem data={data} key={index} />;
        })}
      </div>
    </div>
  );
};

export default MapLegends;
