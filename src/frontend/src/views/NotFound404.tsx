import React from 'react';
import NotFound from '@/assets/images/page-not-found.png';
import Button from '@/components/common/Button';
import { useNavigate } from 'react-router-dom';

const ProjectNotFound = () => {
  const navigate = useNavigate();
  return (
    <div className="md:fmtm-px-[2rem] lg:fmtm-px-[4.5rem] fmtm-h-full fmtm-bg-white">
      <div className="fmtm-flex fmtm-flex-col fmtm-items-center fmtm-h-[90%] fmtm-justify-center fmtm-gap-[3rem] sm:fmtm-gap-[3.75rem]">
        <div>
          <img src={NotFound} alt="Project Not Found Photo" className="fmtm-w-[12rem] lg:fmtm-w-[16.75rem]" />
        </div>
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-3">
          <h2 className="fmtm-text-[1.5rem] md:fmtm-text-[2rem] lg:fmtm-text-[2.5rem] fmtm-text-[#4F4F4F] fmtm-font-barlow fmtm-font-bold fmtm-text-center">
            404
          </h2>
          <p className="fmtm-text-sm sm:fmtm-text-base fmtm-text-center fmtm-text-[#4F4F4F] fmtm-uppercase fmtm-font-semibold">
            Page Not Found
          </p>
        </div>
        <Button
          btnText="Return Home"
          onClick={() => navigate('/')}
          btnType="other"
          className="fmtm-mx-auto fmtm-rounded-none fmtm-py-2"
        />
      </div>
    </div>
  );
};

export default ProjectNotFound;
