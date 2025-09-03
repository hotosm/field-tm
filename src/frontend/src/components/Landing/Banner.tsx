import React from 'react';
import landingbg from '@/assets/images/landing-bg.jpg';

const Banner = () => {
  return (
    <div
      style={{ backgroundImage: `url(${landingbg})` }}
      className={`fmtm-w-full fmtm-h-[38rem] fmtm-bg-no-repeat fmtm-bg-cover fmtm-relative fmtm-flex fmtm-items-center`}
    >
      <div className="fmtm-absolute fmtm-left-0 fmtm-top-0 fmtm-w-full fmtm-h-full fmtm-bg-black/40 fmtm-z-10" />
      <div className="fmtm-text-white fmtm-z-50 fmtm-relative fmtm-ml-[10%]">
        <h1>FIELD - TASKING MANAGER</h1>
        <h4>
          Enhancing field mapping efficiency and accuracy <br /> through seamless coordination
        </h4>
      </div>
    </div>
  );
};

export default Banner;
