import React from 'react';
import AssetModules from '../../shared/AssetModules.js';
import CoreModules from '../../shared/CoreModules';
import { ProjectActions } from '../../store/slices/ProjectSlice';

const MobileFooter = () => {
  const dispatch = CoreModules.useAppDispatch();
  const mobileFooterSelection = CoreModules.useAppSelector((state) => state.project.mobileFooterSelection);

  const footerItem = [
    {
      id: 'explore',
      title: 'Explore',
      icon: (
        <AssetModules.LocationOnIcon
          className={`${
            mobileFooterSelection === 'explore' ? 'fmtm-text-primaryRed' : 'fmtm-text-gray-500'
          } fmtm-duration-300`}
        />
      ),
    },
    {
      id: 'projectInfo',
      title: 'Project Info',
      icon: (
        <AssetModules.InfoIcon
          className={`${
            mobileFooterSelection === 'projectInfo' ? 'fmtm-text-primaryRed' : 'fmtm-text-gray-500'
          } fmtm-duration-300`}
        />
      ),
    },
    {
      id: 'activities',
      title: 'Activities',
      icon: (
        <AssetModules.TaskIcon
          className={`${
            mobileFooterSelection === 'activities' ? 'fmtm-text-primaryRed' : 'fmtm-text-gray-500'
          } fmtm-duration-300`}
        />
      ),
    },
    {
      id: 'mapLegend',
      title: 'Legend',
      icon: (
        <AssetModules.LegendToggleIcon
          className={`${
            mobileFooterSelection === 'mapLegend' ? 'fmtm-text-primaryRed' : 'fmtm-text-gray-500'
          } fmtm-duration-300`}
        />
      ),
    },
    ,
    {
      id: 'others',
      title: 'Others',
      icon: (
        <AssetModules.MoreVertIcon
          className={`${
            mobileFooterSelection === 'others' ? 'fmtm-text-primaryRed' : 'fmtm-text-gray-500'
          } fmtm-duration-300`}
        />
      ),
    },
  ];
  const FooterItemList = ({ item }) => {
    return (
      <div
        onClick={() => dispatch(ProjectActions.SetMobileFooterSelection(item?.id))}
        className="fmtm-group fmtm-cursor-pointer"
      >
        <div
          className={`fmtm-w-full fmtm-flex fmtm-justify-center fmtm-py-1 fmtm-rounded-3xl fmtm-mb-1 fmtm-duration-300 ${
            mobileFooterSelection === item?.id ? 'fmtm-bg-red-100' : 'group-hover:fmtm-bg-gray-200'
          }`}
        >
          <div>{item?.icon}</div>
        </div>
        <div className="fmtm-flex fmtm-justify-center">
          <p
            className={`${
              mobileFooterSelection === item?.id ? 'fmtm-text-primaryRed' : 'fmtm-text-gray-500'
            } fmtm-duration-300 fmtm-text-xs fmtm-whitespace-nowrap`}
          >
            {item?.title}
          </p>
        </div>
      </div>
    );
  };
  return (
    <div className="fmtm-absolute fmtm-bottom-0 sm:fmtm-hidden fmtm-w-full fmtm-border-t-[1px]">
      <div
        className={`fmtm-w-full fmtm-grid fmtm-grid-cols-5 fmtm-bg-white  fmtm-pb-16 fmtm-pt-2 fmtm-gap-5 fmtm-px-2`}
      >
        {footerItem.map((item) => (
          <FooterItemList key={item?.id} item={item} />
        ))}
      </div>
    </div>
  );
};

export default MobileFooter;
