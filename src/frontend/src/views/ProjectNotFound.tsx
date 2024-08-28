import React from 'react';
import NoFileImage from '@/assets/images/no-file.png';
import Button from '@/components/common/Button';
import { useNavigate } from 'react-router-dom';

const ProjectNotFound = () => {
  const navigate = useNavigate();
  return (
    <div className="md:fmtm-px-[2rem] lg:fmtm-px-[4.5rem] fmtm-h-full">
      <div className="fmtm-flex fmtm-flex-col fmtm-items-center fmtm-h-[90%] fmtm-justify-center">
        <div className="fmtm-mb-[5rem]">
          <img src={NoFileImage} alt="Project Not Found Photo" className="fmtm-w-[12rem] lg:fmtm-w-[15.625rem]" />
        </div>
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-3">
          <h2 className="fmtm-text-[1.5rem] md:fmtm-text-[2rem] lg:fmtm-text-[2.5rem] fmtm-text-primaryRed fmtm-font-barlow fmtm-font-bold fmtm-text-center">
            PROJECT NOT FOUND
          </h2>
          <p className="fmtm-text-sm sm:fmtm-text-base fmtm-text-center fmtm-text-[#68707F]">
            There is no project to show, please create a project by clicking the button below.{' '}
          </p>
        </div>
        <Button
          btnText="Create Project"
          onClick={() => navigate('/create-project')}
          btnType="primary"
          className="fmtm-mx-auto fmtm-rounded-none fmtm-py-2 fmtm-mt-8"
        />
      </div>
    </div>
  );
};

export default ProjectNotFound;
