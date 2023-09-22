/* eslint-disable react/no-unstable-nested-components */
import React from 'react';

interface IInputTextFieldProps {
  id?: string;
  label: string;
  rows: number;
  onChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  errorMsg?: string;
  value: string;
  placeholder?: string;
  name?: string;
  classNames?: string;
  maxLength?: number;
  disabled?: boolean;
  required?: boolean;
}

function TextArea({
  id,
  label,
  rows,
  onChange,
  errorMsg,
  value,
  placeholder,
  name,
  classNames,
  maxLength,
  disabled,
  required,
}: IInputTextFieldProps) {
  return (
    <div className={`fmtm-custom-textField ${classNames}`}>
      <div className="fmtm-flex fmtm-gap-1">
        <p className="fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold">{label}</p>
        {required && <p className="fmtm-text-red-500 fmtm-text-[1.2rem]">*</p>}
      </div>
      <div
        className={`fmtm-border-[1px] fmtm-border-gray-300 fmtm-bg-inactive_bg fmtm-w-full fmtm-justify-between fmtm-flex fmtm-items-center fmtm-overflow-hidden`}
      >
        <textarea
          id={id}
          name={name}
          rows={rows}
          className={`fmtm-w-full fmtm-pr-3 fmtm-px-3 focus:fmtm-outline-none fmtm-resize-none ${
            disabled && 'fmtm-bg-gray-400 fmtm-cursor-not-allowed '
          } fmtm-bg-white fmtm-py-[10px] fmtm-text-[1rem]`}
          placeholder={placeholder}
          value={value}
          maxLength={maxLength}
          onChange={onChange}
          disabled={disabled}
        />
      </div>
      {errorMsg && <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">{errorMsg}</p>}
    </div>
  );
}

export default TextArea;
