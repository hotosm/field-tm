import React from 'react';

const MappingHeader = () => {
  return (
    <div className="fmtm-flex fmtm-justify-between fmtm-px-[0.938rem] fmtm-py-[0.625rem]">
      <p className="fmtm-text-[0.813rem] fmtm-text-primaryRed">Mapping our world together</p>
      <a
        href="https://www.hotosm.org/"
        className="fmtm-text-[0.813rem] fmtm-text-primaryRed fmtm-cursor-pointer"
        target="_"
      >
        hotosm.org
      </a>
    </div>
  );
};

export default MappingHeader;
