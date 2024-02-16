/* eslint-disable react/no-unstable-nested-components */
import React from 'react';
// import PropTypes from 'prop-types';
export const blockInvalidChar = (e) => ['e', 'E', '+', '-'].includes(e.key) && e.preventDefault();

interface IInputTextFieldProps {
  id?: string;
  label?: string;
  subLabel?: string | React.JSX.Element;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onKeyDown?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  errorMsg?: string;
  value: string;
  placeholder?: string;
  fieldType: string;
  name?: string;
  flag?: string;
  classNames?: string;
  maxRange?: string;
  minRange?: string;
  maxLength?: number;
  disabled?: boolean;
  required?: boolean;
}

function InputTextField({
  id,
  label,
  subLabel,
  onChange,
  onKeyDown,
  errorMsg,
  value,
  placeholder,
  fieldType,
  name,
  flag,
  classNames,
  maxRange,
  minRange,
  maxLength,
  disabled,
  required,
}: IInputTextFieldProps) {
  return (
    <div className={`fmtm-custom-textField ${classNames}`}>
      {label && (
        <div className="fmtm-mb-2">
          <div className="fmtm-flex fmtm-gap-1">
            <p className="fmtm-text-[1rem] fmtm-font-semibold">{label}</p>
            {required && <p className="fmtm-text-red-500 fmtm-text-[1.2rem]">*</p>}
          </div>
          {subLabel && <p className="fmtm-text-base fmtm-text-[#7A7676]">{subLabel}</p>}
        </div>
      )}
      <div
        className={`fmtm-border-[1px] fmtm-border-gray-300 fmtm-h-[2.3rem] fmtm-w-full fmtm-justify-between fmtm-flex fmtm-items-center fmtm-overflow-hidden fmtm-rounded-md`}
      >
        <input
          id={id}
          type={fieldType}
          name={name}
          className={`fmtm-w-full fmtm-pr-3 fmtm-px-3 focus:fmtm-outline-none ${
            disabled && 'fmtm-bg-gray-400 fmtm-cursor-not-allowed'
          } fmtm-bg-white fmtm-py-[10px] fmtm-text-[1rem]`}
          placeholder={placeholder}
          value={value}
          min={minRange}
          max={maxRange}
          maxLength={maxLength}
          onChange={onChange}
          disabled={disabled}
          onKeyDown={onKeyDown}
        />
      </div>
      {errorMsg && <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">{errorMsg}</p>}
    </div>
  );
}

export default InputTextField;
