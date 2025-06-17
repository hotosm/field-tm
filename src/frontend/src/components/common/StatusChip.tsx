import React from 'react';

type statusType = 'default' | 'info' | 'success' | 'pending' | 'error';
type statusChipPropType = {
  status: statusType;
  label: string;
  filled?: boolean;
};

const getStyle = (status: statusType, filled?: boolean) => {
  switch (status) {
    case 'default':
      return `fmtm-text-grey-700 fmtm-border-grey-700 ${filled && 'fmtm-bg-grey-100'}`;
    case 'info':
      return `fmtm-text-[#417EC9] fmtm-border-[#417EC9] ${filled && 'fmtm-bg-[#e6f0fc]'}`;
    case 'success':
      return `fmtm-text-[#067647] fmtm-border-[#80D89F] ${filled && 'fmtm-bg-[#ECFDF3]'}`;
    case 'pending':
      return `fmtm-text-[#CF9600] fmtm-border-[#F6D480] ${filled && 'fmtm-bg-[#FFF7E4]'}`;
    case 'error':
      return `fmtm-text-[#C61231] fmtm-border-[#E38796] ${filled && 'fmtm-bg-[#FFE9EC]'}`;
  }
};

const StatusChip = ({ status, label, filled }: statusChipPropType) => {
  return (
    <div
      className={`${getStyle(
        status,
        filled,
      )} fmtm-w-fit fmtm-rounded-2xl fmtm-border-[1px] fmtm-px-2 fmtm-text-[0.75rem] fmtm-capitalize fmtm-leading-5`}
    >
      {label}
    </div>
  );
};

export default StatusChip;
