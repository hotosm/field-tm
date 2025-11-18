import React from 'react';
import { Tooltip } from '@mui/material';

type toggleProps = {
  label: string;
  isToggled: boolean;
  onToggle: (state: boolean) => void;
  tooltipMessage?: string;
};

const Toggle = ({ label, isToggled, onToggle, tooltipMessage = '' }: toggleProps) => {
  return (
    <Tooltip title={tooltipMessage} placement="bottom" arrow>
      <div
        onClick={() => onToggle(!isToggled)}
        className={`${isToggled ? 'fmtm-bg-red-light fmtm-text-red-medium fmtm-border-red-medium' : 'fmtm-bg-white fmtm-text-grey-600 fmtm-border-grey-600'} fmtm-border fmtm-px-3 fmtm-py-1 fmtm-cursor-pointer hover:fmtm-text-red-medium hover:fmtm-border-red-medium fmtm-text-base fmtm-rounded fmtm-duration-150`}
      >
        {label}
      </div>
    </Tooltip>
  );
};

export default Toggle;
