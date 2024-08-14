import React from 'react';
import AssetModules from '@/shared/AssetModules.js';
import { useNavigate } from 'react-router-dom';

const CreateEditOrganizationHeader = ({ organizationId }: { organizationId: string }) => {
  const navigate = useNavigate();
  return (
    <div className="fmtm-border-b-white fmtm-border-b-[1px] fmtm-bg-[#F5F5F5]">
      <div className="fmtm-flex fmtm-justify-between fmtm-items-center">
        <div className="fmtm-pb-1">
          <h1 className="sm:fmtm-text-xl md:fmtm-text-2xl">
            {organizationId ? 'EDIT YOUR ORGANIZATION' : 'REGISTER YOUR ORGANIZATION'}
          </h1>
        </div>
        <div
          className="hover:fmtm-bg-gray-200 fmtm-rounded-full fmtm-p-2 fmtm-duration-300 fmtm-cursor-pointer"
          onClick={() => navigate('/organisation')}
        >
          <AssetModules.CloseIcon />
        </div>
      </div>
    </div>
  );
};

export default CreateEditOrganizationHeader;
