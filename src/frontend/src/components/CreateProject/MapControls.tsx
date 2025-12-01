import React from 'react';
import AssetModules from '@/shared/AssetModules';
import LayerSwitchMenu from '../MapComponent/OpenLayersComponent/LayerSwitcher/LayerSwitchMenu';
import { Tooltip } from '@mui/material';

type mapControlComponentType = {
  map: any;
  toggleEdit?: boolean;
  setToggleEdit?: (value: boolean) => void;
};

const MapControls = ({ map, toggleEdit, setToggleEdit }: mapControlComponentType) => {
  const btnList = [
    {
      id: 'add',
      icon: <AssetModules.AddIcon className="!fmtm-text-[1rem]" />,
      title: 'Zoom In',
      show: true,
    },
    {
      id: 'minus',
      icon: <AssetModules.RemoveIcon className="!fmtm-text-[1rem]" />,
      title: 'Zoom Out',
      show: true,
    },
    {
      id: 'edit',
      icon: (
        <AssetModules.TimelineIcon
          className={`${toggleEdit ? 'fmtm-text-primaryRed' : 'fmtm-text-[#666666]'} !fmtm-text-[1rem]`}
        />
      ),
      title: 'Edit Project Boundary',
      show: !!setToggleEdit,
    },
  ];

  const handleOnClick = (btnId) => {
    const actualZoom = map.getView().getZoom();
    if (btnId === 'add') {
      map.getView().setZoom(actualZoom + 1);
    } else if (btnId === 'minus') {
      map.getView().setZoom(actualZoom - 1);
    } else if (btnId === 'edit' && setToggleEdit) {
      setToggleEdit(!toggleEdit);
    }
  };

  return (
    <div className="fmtm-absolute fmtm-bottom-24 md:fmtm-bottom-10 fmtm-right-3 fmtm-z-[45] fmtm-flex fmtm-flex-col fmtm-items-center fmtm-gap-3">
      <LayerSwitchMenu map={map} />
      <div className="fmtm-rounded fmtm-overflow-hidden fmtm-w-fit">
        {btnList.map((btn) => (
          <div key={btn.id} className={`${!btn.show && 'fmtm-hidden'} fmtm-border-t first:fmtm-border-white`}>
            <Tooltip title={btn.title} placement="left" arrow key={btn.title}>
              <div
                className="fmtm-bg-white hover:fmtm-bg-gray-100 fmtm-cursor-pointer fmtm-duration-300 fmtm-w-7 fmtm-h-7 fmtm-flex fmtm-justify-center fmtm-items-center "
                onClick={() => handleOnClick(btn.id)}
              >
                {btn.icon}
              </div>
            </Tooltip>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MapControls;
