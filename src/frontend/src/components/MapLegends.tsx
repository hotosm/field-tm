import React from 'react';
import AssetModules from '@/shared/AssetModules';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuPortal,
} from '@/components/common/Dropdown';
import { Tooltip } from '@mui/material';

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
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger className="fmtm-outline-none">
        <Tooltip title="Legend Toggle" placement="left">
          <div
            className={`fmtm-bg-white fmtm-rounded-full hover:fmtm-bg-gray-100 fmtm-cursor-pointer fmtm-duration-300 fmtm-w-9 fmtm-h-9 fmtm-min-h-9 fmtm-min-w-9 fmtm-max-w-9 fmtm-max-h-9 fmtm-flex fmtm-justify-center fmtm-items-center `}
          >
            <AssetModules.LegendToggleIcon />
          </div>
        </Tooltip>
      </DropdownMenuTrigger>
      <DropdownMenuPortal>
        <DropdownMenuContent
          className="fmtm-px-2 fmtm-border-none fmtm-z-[60px] fmtm-bg-white"
          align="end"
          alignOffset={100}
          sideOffset={-42}
        >
          <div className="fmtm-py-3">
            <p className="fmtm-mb-3">Legend</p>
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
              {MapDetails.map((data, index) => {
                return <LegendListItem data={data} key={index} />;
              })}
            </div>
          </div>{' '}
        </DropdownMenuContent>
      </DropdownMenuPortal>
    </DropdownMenu>
  );
};

export default MapLegends;
