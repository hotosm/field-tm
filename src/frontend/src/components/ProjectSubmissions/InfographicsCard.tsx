import React from 'react';
import handleDownload from '@/utilfunctions/downloadChart';
import AssetModules from '@/shared/AssetModules.js';

type InfographicsCardType = {
  header: string;
  subHeader?: React.ReactElement;
  body: React.ReactElement;
  cardRef?: React.MutableRefObject<null> | undefined;
};

const InfographicsCard = ({ header, subHeader, body, cardRef }: InfographicsCardType) => (
  <div
    ref={cardRef}
    className="fmtm-w-full fmtm-h-[24rem] fmtm-bg-white fmtm-flex fmtm-flex-col fmtm-gap-5 fmtm-p-5 fmtm-rounded-xl"
  >
    <div className="fmtm-flex fmtm-items-end fmtm-justify-between">
      <h5 className="fmtm-text-lg">{header}</h5>
      <div
        data-html2canvas-ignore="true"
        onClick={() => handleDownload(cardRef, header)}
        className="group fmtm-rounded-full fmtm-p-1 hover:fmtm-bg-gray-200 fmtm-cursor-pointer fmtm-duration-150 fmtm-h-9 fmtm-w-9 fmtm-flex fmtm-items-center fmtm-justify-center"
      >
        <AssetModules.FileDownloadOutlinedIcon />
      </div>
    </div>
    {subHeader && subHeader}
    <div className="fmtm-h-[80%]">{body}</div>
  </div>
);

export default InfographicsCard;
