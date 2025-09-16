import React from 'react';
import { useNavigate } from 'react-router-dom';
import landingbg from '@/assets/images/landing-bg.jpg';
import Button from '@/components/common/Button';

const Banner = () => {
  const navigate = useNavigate();

  return (
    <div
      style={{ backgroundImage: `url(${landingbg})` }}
      className={`fmtm-w-full fmtm-h-[38rem] fmtm-bg-no-repeat fmtm-bg-cover fmtm-relative fmtm-flex fmtm-items-center`}
    >
      <div className="fmtm-absolute fmtm-left-0 fmtm-top-0 fmtm-w-full fmtm-h-full fmtm-bg-black/40 fmtm-z-10" />
      <div className="fmtm-text-white fmtm-z-50 fmtm-relative fmtm-ml-[10%] fmtm-flex fmtm-flex-col fmtm-gap-y-5">
        <h1 className="fmtm-text-[2.5rem] md:fmtm-text-[3.625rem]">FIELD - TASKING MANAGER</h1>
        <h4 className="fmtm-text-[1rem] md:fmtm-text-[1.25rem] ">
          Enhancing field mapping efficiency and accuracy <br /> through seamless coordination
        </h4>
        <Button variant="primary-red" onClick={() => navigate('/explore')}>
          EXPLORE PROJECTS
        </Button>
      </div>
    </div>
  );
};

export default Banner;
