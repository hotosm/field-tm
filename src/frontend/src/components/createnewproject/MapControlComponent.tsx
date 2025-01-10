import React from 'react';
import AssetModules from '@/shared/AssetModules';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';

const MapControlComponent = ({ map, hasEditUndo }) => {
  const dispatch = useAppDispatch();
  const toggleSplittedGeojsonEdit = useAppSelector((state) => state.createproject.toggleSplittedGeojsonEdit);
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
      id: 'Edit',
      icon: (
        <AssetModules.TimelineIcon
          style={{ fontSize: '20px' }}
          className={`${toggleSplittedGeojsonEdit ? 'fmtm-text-primaryRed' : 'fmtm-text-[#666666]'}`}
        />
      ),
    },
  ];

  const handleOnClick = (btnId) => {
    if (btnId === 'Add') {
      const actualZoom = map.getView().getZoom();
      map.getView().setZoom(actualZoom + 1);
    } else if (btnId === 'Minus') {
      const actualZoom = map.getView().getZoom();
      map.getView().setZoom(actualZoom - 1);
    } else if (btnId === 'Edit') {
      dispatch(CreateProjectActions.SetToggleSplittedGeojsonEdit(!toggleSplittedGeojsonEdit));
    }
  };

  return (
    <div className="fmtm-absolute fmtm-top-[20px] fmtm-left-3 fmtm-z-50 fmtm-bg-white fmtm-rounded-md fmtm-p-[2px] fmtm-shadow-xl fmtm-flex fmtm-flex-col fmtm-gap-[2px]">
      {btnList.map((btn) => {
        return (
          <div key={btn.id} title={btn.id}>
            {((btn.id !== 'Edit' && btn.id !== 'Undo') || (btn.id === 'Edit' && hasEditUndo)) && (
              <div
                className={` fmtm-p-1 fmtm-rounded-md fmtm-duration-200 fmtm-cursor-pointer ${
                  toggleSplittedGeojsonEdit && btn.id === 'Edit'
                    ? 'fmtm-bg-red-50'
                    : 'fmtm-bg-white hover:fmtm-bg-gray-100'
                }`}
                onClick={() => handleOnClick(btn.id)}
              >
                {btn.icon}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default MapControlComponent;
