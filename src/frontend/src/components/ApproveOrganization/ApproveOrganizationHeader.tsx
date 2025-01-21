import React from 'react';
import AssetModules from '@/shared/AssetModules.js';
import { useNavigate } from 'react-router-dom';

const ApproveOrganizationHeader = () => {
  const navigate = useNavigate();
  return (
    <div className="fmtm-px-5 fmtm-border-b-white fmtm-border-[1px] fmtm-bg-[#F5F5F5]">
      <div className="fmtm-flex fmtm-justify-between fmtm-items-center">
        <div className="fmtm-pt-3 fmtm-pb-1">
          <h1 className="sm:fmtm-text-xl md:fmtm-text-2xl">APPROVE ORGANIZATION</h1>
        </div>
        <div
          className="hover:fmtm-bg-gray-200 fmtm-rounded-full fmtm-p-2 fmtm-duration-300 fmtm-cursor-pointer"
          onClick={() => navigate('/organization')}
        >
          <AssetModules.CloseIcon />
        </div>
      </div>
    </div>
  );
};

export default ApproveOrganizationHeader;
