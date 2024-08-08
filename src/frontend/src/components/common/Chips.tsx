import React from 'react';
import AssetModule from '../../shared/AssetModules.js';

type chipsType = {
  data: string[];
  clearChip: (i: number) => void;
};

const Chips = ({ data, clearChip }: chipsType) => {
  return (
    <div className="fmtm-flex fmtm-gap-2 fmtm-items-center fmtm-flex-wrap fmtm-my-2">
      {data.map((item: string, i: number) => (
        <div
          key={i}
          className="fmtm-px-2 fmtm-py-1 fmtm-border-[1px] fmtm-border-[#D7D7D7] fmtm-rounded-[40px] fmtm-flex fmtm-w-fit fmtm-items-center fmtm-gap-1"
        >
          <p>{item}</p>
          <AssetModule.CloseIcon
            style={{ fontSize: '20px' }}
            className="hover:fmtm-text-primaryRed fmtm-cursor-pointer fmtm-duration-300"
            onClick={() => clearChip(i)}
          />
        </div>
      ))}
    </div>
  );
};

export default Chips;
