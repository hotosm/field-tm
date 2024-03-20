import React, { useState } from 'react';
import AssetModules from '@/shared/AssetModules';
import VectorLayer from 'ol/layer/Vector';
import CoreModules from '@/shared/CoreModules.js';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { useAppSelector } from '@/types/reduxTypes';

const MapControlComponent = ({ map }) => {
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
  const dispatch = CoreModules.useAppDispatch();
  const [toggleCurrentLoc, setToggleCurrentLoc] = useState(false);
  const geolocationStatus = useAppSelector((state) => state.project.geolocationStatus);
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
            className="fmtm-bg-white fmtm-rounded-full fmtm-p-2 hover:fmtm-bg-gray-100 fmtm-cursor-pointer fmtm-duration-300"
            onClick={() => handleOnClick(btn.id)}
            title={btn.title}
          >
            {btn.icon}
          </div>
        </div>
      ))}
    </div>
  );
};

export default MapControlComponent;
