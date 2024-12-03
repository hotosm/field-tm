import React from 'react';
import AssetModules from '@/shared/AssetModules';
import VectorLayer from 'ol/layer/Vector';
import * as olExtent from 'ol/extent';

const MapControlComponent = ({ map }) => {
  const btnList = [
    {
      id: 'Add',
      icon: <AssetModules.AddIcon style={{ fontSize: '20px' }} className="fmtm-text-[#666666]" />,
    },
    {
      id: 'Minus',
      icon: <AssetModules.RemoveIcon style={{ fontSize: '20px' }} className="fmtm-text-[#666666]" />,
    },
    {
      id: 'Zoom To Layer',
      icon: <AssetModules.CropFreeIcon style={{ fontSize: '20px' }} className="fmtm-text-[#666666]" />,
    },
  ];

  const handleOnClick = (btnId) => {
    if (btnId === 'Add') {
      const actualZoom = map.getView().getZoom();
      map.getView().setZoom(actualZoom + 1);
    } else if (btnId === 'Minus') {
      const actualZoom = map.getView().getZoom();
      map.getView().setZoom(actualZoom - 1);
    } else if (btnId === 'Zoom To Layer') {
      const extent = olExtent.createEmpty();
      const layers = map?.getLayers();

      layers?.forEach((layer) => {
        if (layer instanceof VectorLayer) {
          olExtent.extend(extent, layer.getSource().getExtent());
        }
      });
      map?.getView()?.fit(extent, {
        padding: [50, 50, 50, 50],
        duration: 900,
      });
    }
  };

  return (
    <div className="fmtm-absolute fmtm-top-[20px] fmtm-left-3 fmtm-z-50 fmtm-bg-white fmtm-rounded-md fmtm-p-[2px] fmtm-shadow-xl fmtm-flex fmtm-flex-col fmtm-gap-[2px]">
      {btnList.map((btn) => {
        return (
          <div key={btn.id} title={btn.id}>
            <div
              className={`fmtm-p-1 fmtm-rounded-md fmtm-duration-200 fmtm-cursor-pointer hover:fmtm-bg-red-50`}
              onClick={() => handleOnClick(btn.id)}
            >
              {btn.icon}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default MapControlComponent;
