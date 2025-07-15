import React from 'react';
import AssetModules from '@/shared/AssetModules.js';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { Link, useParams } from 'react-router-dom';

type footerItemType = {
  id: string;
  title: string;
  icon: React.ReactNode;
};

const MobileFooter = () => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const mobileFooterSelection = useAppSelector((state) => state.project.mobileFooterSelection);
  const taskModalStatus = useAppSelector((state) => state.project.taskModalStatus);

  const footerItem: footerItemType[] = [
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
      id: 'instructions',
      title: 'Instructions',
      icon: (
        <AssetModules.IntegrationInstructionsIcon
          className={`${
            mobileFooterSelection === 'instructions' ? 'fmtm-text-primaryRed' : 'fmtm-text-gray-500'
          } fmtm-duration-300`}
        />
      ),
    },
    {
      id: 'comment',
      title: 'Comment',
      icon: (
        <AssetModules.QuestionAnswerIcon
          className={`${
            mobileFooterSelection === 'comment' ? 'fmtm-text-primaryRed' : 'fmtm-text-gray-500'
          } fmtm-duration-300`}
        />
      ),
    },
  ];

  const infographicFooterItem: footerItemType = {
    id: 'infographics',
    title: 'Infographics',
    icon: <AssetModules.BarChartIcon className={`fmtm-text-gray-500 hover:fmtm-text-primaryRed fmtm-duration-300`} />,
  };

  const FooterItemList = ({ item }) => {
    return (
      <div
        onClick={() => dispatch(ProjectActions.SetMobileFooterSelection(item?.id))}
        className={`fmtm-group fmtm-cursor-pointer ${item.id === 'comment' && !taskModalStatus ? 'fmtm-hidden' : ''}`}
      >
        <div
          className={`fmtm-w-full fmtm-flex fmtm-justify-center fmtm-py-1 fmtm-rounded-3xl fmtm-mb-1 fmtm-duration-300 ${
            mobileFooterSelection === item?.id && mobileFooterSelection !== 'infographics'
              ? 'fmtm-bg-red-100'
              : 'group-hover:fmtm-bg-gray-200'
          }`}
        >
          <div>{item?.icon}</div>
        </div>
        <div className="fmtm-flex fmtm-justify-center">
          <p
            className={`${
              mobileFooterSelection === item?.id && mobileFooterSelection !== 'infographics'
                ? 'fmtm-text-primaryRed'
                : 'fmtm-text-gray-500'
            } fmtm-duration-300 fmtm-text-xs fmtm-whitespace-nowrap`}
          >
            {item?.title}
          </p>
        </div>
      </div>
    );
  };
  return (
    <div className="fmtm-absolute fmtm-bottom-0 md:fmtm-hidden fmtm-w-full fmtm-border-t-[1px] fmtm-z-[10008]">
      <div
        className={`fmtm-w-full fmtm-grid ${
          taskModalStatus ? 'fmtm-grid-cols-5' : 'fmtm-grid-cols-4'
        } fmtm-bg-white fmtm-pb-2 fmtm-pt-2 fmtm-gap-5 fmtm-px-2`}
      >
        {footerItem.map((item) => (
          <FooterItemList key={item?.id} item={item} />
        ))}
        <Link to={`/project-submissions/${params.id}?tab=infographics`}>
          <FooterItemList item={infographicFooterItem} />
        </Link>
      </div>
    </div>
  );
};

export default MobileFooter;
