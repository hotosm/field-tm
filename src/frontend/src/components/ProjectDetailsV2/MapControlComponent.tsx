import React, { useState } from 'react';
import AssetModules from '@/shared/AssetModules';
import VectorLayer from 'ol/layer/Vector';
import CoreModules from '@/shared/CoreModules.js';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { useAppSelector } from '@/types/reduxTypes';
import { useLocation } from 'react-router-dom';
import ProjectOptions from '@/components/ProjectDetailsV2/ProjectOptions';
import useOutsideClick from '@/hooks/useOutsideClick';

type mapControlComponentType = {
  map: any;
  projectName: string;
};

const MapControlComponent = ({ map, projectName }: mapControlComponentType) => {
  const btnList = [
    {
      id: 'add',
      icon: <AssetModules.AddIcon />,
      title: 'Zoom In',
    },
    {
      id: 'minus',
      icon: <AssetModules.RemoveIcon />,
      title: 'Zoom Out',
    },
    {
      id: 'currentLocation',
      icon: <AssetModules.MyLocationIcon />,
      title: 'My Location',
    },
    {
      id: 'taskBoundries',
      icon: <AssetModules.CropFreeIcon />,
      title: 'Zoom to Project',
    },
  ];

  const { pathname } = useLocation();
  const dispatch = CoreModules.useAppDispatch();
  const [toggleCurrentLoc, setToggleCurrentLoc] = useState(false);
  const geolocationStatus = useAppSelector((state) => state.project.geolocationStatus);
  const [divRef, toggle, handleToggle] = useOutsideClick();

  const handleOnClick = (btnId) => {
    if (btnId === 'add') {
      const actualZoom = map.getView().getZoom();
      map.getView().setZoom(actualZoom + 1);
    } else if (btnId === 'minus') {
      const actualZoom = map.getView().getZoom();
      map.getView().setZoom(actualZoom - 1);
    } else if (btnId === 'currentLocation') {
      setToggleCurrentLoc(!toggleCurrentLoc);
      dispatch(ProjectActions.ToggleGeolocationStatus(!geolocationStatus));
    } else if (btnId === 'taskBoundries') {
      const layers = map.getAllLayers();
      let extent;
      layers.map((layer) => {
        if (layer instanceof VectorLayer) {
          const layerName = layer.getProperties().name;
          if (layerName === 'project-area') {
            extent = layer.getSource().getExtent();
          }
        }
      });
      map.getView().fit(extent, {
        padding: [10, 10, 10, 10],
      });
    }
  };

  return (
    <div className="fmtm-absolute fmtm-top-16 fmtm-right-3 fmtm-z-[99] fmtm-flex fmtm-flex-col fmtm-gap-4">
      {btnList.map((btn) => (
        <div key={btn.id}>
          <div
            className={`fmtm-bg-white fmtm-rounded-full fmtm-p-2 hover:fmtm-bg-gray-100 fmtm-cursor-pointer fmtm-duration-300 ${
              geolocationStatus && btn.id === 'currentLocation' ? 'fmtm-text-primaryRed' : ''
            }`}
            onClick={() => handleOnClick(btn.id)}
            title={btn.title}
          >
            {btn.icon}
          </div>
        </div>
      ))}
      <div
        className={`fmtm-relative ${!pathname.includes('project/') ? 'fmtm-hidden' : 'sm:fmtm-hidden'}`}
        ref={divRef}
      >
        <div
          onClick={() => handleToggle()}
          className="fmtm-bg-white fmtm-rounded-full fmtm-p-2 hover:fmtm-bg-gray-100 fmtm-cursor-pointer fmtm-duration-300 "
        >
          <AssetModules.FileDownloadIcon />
        </div>
        <div
          className={`fmtm-flex fmtm-gap-4 fmtm-absolute fmtm-duration-200 fmtm-z-[1000] fmtm-bg-white fmtm-p-2 fmtm-rounded-md ${
            toggle
              ? 'fmtm-right-[3rem] fmtm-top-0 md:fmtm-top-0 sm:fmtm-hidden'
              : '-fmtm-right-[60rem] fmtm-top-0 sm:fmtm-hidden'
          }`}
        >
          <ProjectOptions projectName={projectName} />
        </div>
      </div>
    </div>
  );
};

export default MapControlComponent;
