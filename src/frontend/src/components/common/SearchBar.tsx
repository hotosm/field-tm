import React from 'react';
import { useRef, useEffect } from 'react';
import SearchIcon from '@/assets/icons/searchIcon.svg';
import AssetModules from '@/shared/AssetModules';

interface ISearchbarProps {
  className?: string;
  placeholder?: string;
  value: string | number;
  onChange: (value: any) => void;
  isSmall?: boolean;
  isFocus?: boolean;
  onClick?: () => void;
  onBlur?: () => void;
  required?: boolean;
  wrapperStyle?: string;
}

export default function Searchbar({
  className,
  placeholder = 'Search',
  value,
  onChange,
  isSmall,
  isFocus,
  onClick,
  onBlur,
  wrapperStyle,
  required = true, // in default required is true
}: ISearchbarProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const handleClearSearch = () => {
    onChange({ target: { value: '' } });
    inputRef?.current?.focus();
  };

  useEffect(() => {
    if (!isFocus) return;
    inputRef?.current?.focus();
  }, [isFocus]);

  return (
    <div className={`fmtm-flex fmtm-w-full fmtm-items-center ${isSmall ? 'fmtm-h-10' : 'fmtm-h-12'} ${wrapperStyle} `}>
      <label htmlFor="simple-search" className="fmtm-sr-only">
        {placeholder}
      </label>
      <div className="fmtm-relative fmtm-w-full">
        <div className="fmtm-pointer-events-none fmtm-absolute fmtm-inset-y-0 fmtm-left-0 fmtm-flex fmtm-items-center fmtm-pl-2">
          <img src={SearchIcon} alt="Search Icon" className="fmtm-h-5 fmtm-w-5" />
        </div>
        {value && (
          <div
            className={`fmtm-absolute fmtm-right-2 ${isSmall ? 'fmtm-top-1.5' : 'fmtm-top-[0.563rem]'} fmtm-flex 
        fmtm-cursor-pointer fmtm-items-center fmtm-justify-center fmtm-rounded-full fmtm-bg-grey-100 fmtm-p-1 fmtm-duration-200  hover:fmtm-bg-grey-200`}
            onClick={handleClearSearch}
          >
            <AssetModules.CloseIcon className="!fmtm-text-[14px] fmtm-text-grey-500" />
          </div>
        )}

        <input
          ref={inputRef}
          type="text"
          className={`fmtm-block fmtm-w-full fmtm-rounded-lg fmtm-border  fmtm-border-grey-300
            fmtm-pl-[35px] fmtm-pr-[28px] fmtm-text-base fmtm-font-normal 
            fmtm-text-gray-500 placeholder:fmtm-font-normal placeholder:fmtm-text-gray-500 fmtm-outline-none ${
              isSmall ? 'fmtm-h-[36px] fmtm-py-2' : 'fmtm-h-[40px] fmtm-py-3'
            }
            ${className}`}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          onClick={onClick}
          onBlur={onBlur}
          required={required}
        />
      </div>
    </div>
  );
}
