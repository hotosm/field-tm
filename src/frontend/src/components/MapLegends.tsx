import React, { useState } from 'react';
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
      color: defaultTheme.palette.mapFeatureColors.UNLOCKED_TO_MAP,
      status: 'none',
    },
    {
      value: 'Locked For Mapping',
      color: defaultTheme.palette.mapFeatureColors.LOCKED_FOR_MAPPING,
      status: 'lock',
    },
    {
      value: 'Ready For Validation',
      color: defaultTheme.palette.mapFeatureColors.UNLOCKED_TO_VALIDATE,
      status: 'none',
    },
    {
      value: 'Locked For Validation',
      color: defaultTheme.palette.mapFeatureColors.LOCKED_FOR_VALIDATION,
      status: 'lock',
    },
    {
      value: 'Validated',
      color: defaultTheme.palette.mapFeatureColors.UNLOCKED_DONE,
      status: 'none',
    },
    {
      value: 'Locked',
      color: '',
      status: 'none',
      type: 'locked',
    },
  ];

  const [toggleLegend, setToggleLegend] = useState(true);

  const LegendListItem = ({ data }: { data: mapDetialsType }) => {
    return (
      <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
        {data.type !== 'locked' ? (
          <div
            style={{ backgroundColor: data.color, borderRadius: 0 }}
            color="primary"
            className="!fmtm-w-5 !fmtm-h-5 fmtm-border-[1px] fmtm-border-gray-200"
          ></div>
        ) : (
          <AssetModules.LockIcon className="!fmtm-text-[20px]" />
        )}
        <p className="fmtm-body-sm fmtm-text-[#494949]">{data.value}</p>
      </div>
    );
  };

  return (
    <div className="fmtm-absolute fmtm-bottom-24 md:fmtm-bottom-10 fmtm-left-3 fmtm-z-[45]">
      <DropdownMenu modal={false} open={toggleLegend}>
        <DropdownMenuTrigger className="fmtm-outline-none" onClick={() => setToggleLegend(true)}>
          <Tooltip title="Legend" placement="right" arrow>
            <div
              className={`fmtm-bg-white fmtm-rounded hover:fmtm-bg-gray-100 fmtm-cursor-pointer fmtm-duration-300 fmtm-w-6 fmtm-h-6 fmtm-min-h-6 fmtm-min-w-6 fmtm-max-w-6 fmtm-max-h-6 fmtm-flex fmtm-justify-center fmtm-items-center fmtm-border-[1px]  fmtm-border-grey-300`}
            >
              <AssetModules.LegendToggleIcon className="!fmtm-text-[1rem]" />
            </div>
          </Tooltip>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          className="fmtm-border-none fmtm-bg-white fmtm-p-2 fmtm-z-[45]"
          align="start"
          sideOffset={-25}
        >
          <div className="fmtm-flex fmtm-items-center fmtm-justify-between">
            <p className="fmtm-body-sm-semibold fmtm-mb-2">Legend</p>
            <div
              className="fmtm-p-1 hover:fmtm-bg-grey-200 fmtm-rounded-full fmtm-w-4 fmtm-h-4 fmtm-flex fmtm-items-center fmtm-justify-center fmtm-duration-200"
              onClick={() => setToggleLegend(false)}
            >
              <AssetModules.ExpandMoreIcon className="!fmtm-text-sm fmtm-cursor-pointer" />
            </div>
          </div>
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
            {MapDetails.map((data, index) => {
              return <LegendListItem data={data} key={index} />;
            })}
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

export default MapLegends;
