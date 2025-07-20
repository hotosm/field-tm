import React from 'react';
import UnderConstructionImage from '@/assets/images/under_construction.png';

const UnderConstruction = () => {
  return (
    <div className="md:fmtm-px-[2rem] lg:fmtm-px-[4.5rem] fmtm-h-full">
      <div className="fmtm-flex fmtm-flex-col fmtm-items-center fmtm-h-[90%] fmtm-justify-center fmtm-gap-5">
        <div>
          <img src={UnderConstructionImage} alt="Something Went Wrong Photo" />
        </div>
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-5">
          <h2 className="fmtm-text-[1.5rem] md:fmtm-text-[2rem] lg:fmtm-text-[2.5rem] fmtm-text-[#4F4F4F] fmtm-font-primary fmtm-font-bold fmtm-text-center">
            OOPS !! WE ARE UNDER CONSTRUCTION
          </h2>
          <p className="fmtm-text-sm sm:fmtm-text-base fmtm-font-bold fmtm-text-center fmtm-text-[#4F4F4F]">
            WE WELL BE BACK SOON.
          </p>
        </div>
      </div>
    </div>
  );
};

export default UnderConstruction;
