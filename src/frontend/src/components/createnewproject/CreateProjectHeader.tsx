import React from 'react';
import AssetModules from '@/shared/AssetModules.js';
import { useNavigate } from 'react-router-dom';

const CreateProjectHeader = () => {
  const navigate = useNavigate();
  return (
    <div className="fmtm-border-b fmtm-border-b-white">
      <div className="fmtm-flex fmtm-justify-between fmtm-items-center">
        <div className="fmtm-pb-1">
          <h4>CREATE NEW PROJECT</h4>
          <p className="sm:fmtm-text-sm md:fmtm-text-lg fmtm-text-gray-500">
            Setup your field mapping project following the five comprehensive steps.
          </p>
        </div>
        <div
          className="hover:fmtm-bg-gray-200 fmtm-rounded-full fmtm-p-2 fmtm-duration-300"
          onClick={() => navigate('/')}
        >
          <AssetModules.CloseIcon />
        </div>
      </div>
    </div>
  );
};

export default CreateProjectHeader;
