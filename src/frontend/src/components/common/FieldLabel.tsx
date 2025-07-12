import React from 'react';
import AssetModules from '@/shared/AssetModules';
import { Tooltip } from '@mui/material';

interface IFieldLabelProps {
  label: string | undefined;
  tooltipMessage?: string;
  astric?: boolean;
  id?: string;
  disabled?: boolean;
  className?: string;
  labelClassName?: string;
}

export default function FieldLabel({
  label,
  tooltipMessage,
  astric,
  disabled,
  className,
  labelClassName = '',
}: IFieldLabelProps) {
  return (
    <div
      className={`fmtm-flex fmtm-items-center fmtm-justify-start fmtm-gap-x-[0.375rem] ${className} ${
        disabled ? 'fmtm-text-grey-600' : ''
      }`}
    >
      <div className="fmtm-flex fmtm-items-center">
        <p className={`fmtm-button ${labelClassName}`}>{label}</p>
        {astric && <span className="fmtm-text-red-medium fmtm-button">&nbsp;*</span>}
      </div>
      {tooltipMessage && (
        <Tooltip title={tooltipMessage} placement="right" arrow>
          <AssetModules.InfoOutlineIcon className="fmtm-text-grey-600 !fmtm-text-sm" />
        </Tooltip>
      )}
    </div>
  );
}
