import React from 'react';
import NoFileImage from '@/assets/images/project-not-found.png';
import Button from '@/components/common/Button';
import { useNavigate } from 'react-router-dom';

const ProjectNotFound = () => {
  const navigate = useNavigate();
  return (
    <div className="md:fmtm-px-[2rem] lg:fmtm-px-[4.5rem] fmtm-h-full">
      <div className="fmtm-flex fmtm-flex-col fmtm-items-center fmtm-h-[90%] fmtm-justify-center fmtm-gap-[3rem] sm:fmtm-gap-[5rem]">
        <div>
          <img src={NoFileImage} alt="Project Not Found Photo" className="lg:fmtm-w-[7.688rem]" />
        </div>
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-3">
          <h2 className="fmtm-text-[1.5rem] md:fmtm-text-[2rem] lg:fmtm-text-[2.5rem] fmtm-text-[#4F4F4F] fmtm-font-primary fmtm-font-bold fmtm-text-center">
            PROJECT NOT FOUND
          </h2>
          <p className="fmtm-text-sm sm:fmtm-text-base fmtm-text-center fmtm-text-[#4F4F4F] fmtm-uppercase fmtm-font-semibold">
            There is no project to show
          </p>
        </div>
        <Button variant="secondary-red" onClick={() => navigate('/create-project')}>
          Create Project
        </Button>
      </div>
    </div>
  );
};

export default ProjectNotFound;
