import React from 'react';
import AssetModules from '@/shared/AssetModules';
import { useNavigate } from 'react-router-dom';
import Button from '@/components/common/Button';

const Forbidden = () => {
  const navigate = useNavigate();

  return (
    <div className="md:fmtm-px-[2rem] lg:fmtm-px-[4.5rem] fmtm-h-full fmtm-bg-white">
      <div className="fmtm-flex fmtm-flex-col fmtm-items-center fmtm-h-[90%] fmtm-justify-center fmtm-gap-[3rem] sm:fmtm-gap-[3.75rem]">
        <div>
          <div className="fmtm-bg-red-light fmtm-rounded-full fmtm-p-4">
            <AssetModules.LockIcon className="!fmtm-text-[8rem] fmtm-text-red-medium" />
          </div>
        </div>
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-3">
          <h2 className="fmtm-text-[1.5rem] md:fmtm-text-[2rem] lg:fmtm-text-[2.5rem] fmtm-text-[#4F4F4F] fmtm-font-primary fmtm-font-bold fmtm-text-center">
            403 FORBIDDEN
          </h2>
          <p className="fmtm-text-sm sm:fmtm-text-base fmtm-text-center fmtm-text-[#4F4F4F] fmtm-uppercase fmtm-font-semibold">
            You don't have permission to access this page
          </p>
        </div>
        <Button variant="secondary-red" onClick={() => navigate('/explore')}>
          Return Home
        </Button>
      </div>
    </div>
  );
};

export default Forbidden;
