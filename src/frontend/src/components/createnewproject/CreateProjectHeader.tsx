import React from 'react';
import AssetModules from '../../shared/AssetModules.js';
import { useNavigate } from 'react-router-dom';

const CreateProjectHeader = () => {
  const navigate = useNavigate();
  return (
    <div className="fmtm-px-5 fmtm-border-b-white fmtm-border-[1px] fmtm-bg-gray-100">
      <div className="fmtm-flex fmtm-justify-between fmtm-items-center">
        <div className="fmtm-pt-3 fmtm-pb-1">
          <h1 className="sm:fmtm-text-xl md:fmtm-text-2xl">CREATE NEW PROJECT</h1>
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
