import React from 'react';
import AssetModule from '@/shared/AssetModules';
import isEmpty from '@/utilfunctions/isEmpty.js';

type chipsType = {
  data: string[];
  clearChip: (i: number) => void;
  className?: string;
};

const Chips = ({ data, clearChip, className }: chipsType) => {
  return (
    !isEmpty(data) && (
      <div className={`fmtm-flex fmtm-gap-2 fmtm-items-center ${className}`}>
        {data.map((item: string, i: number) => (
          <div
            key={i}
            className="fmtm-body-md fmtm-px-2 fmtm-border-[1px] fmtm-bg-grey-100 fmtm-rounded-[40px] fmtm-flex fmtm-w-fit fmtm-items-center fmtm-gap-1"
          >
            <p>{item}</p>
            <AssetModule.CloseIcon
              style={{ fontSize: '12px' }}
              className="hover:fmtm-text-primaryRed fmtm-cursor-pointer fmtm-duration-300"
              onClick={() => clearChip(i)}
            />
          </div>
        ))}
      </div>
    )
  );
};

export default Chips;
