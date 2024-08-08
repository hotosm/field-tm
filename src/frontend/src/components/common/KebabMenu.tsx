import React, { useState, useRef, useLayoutEffect, useEffect, useCallback } from 'react';
import AssetModules from '../../shared/AssetModules.js';

type optionType = { id: number | string; icon: React.ReactNode; label: string; onClick: any };

type directionType = 'left-top' | 'left-bottom' | 'right-bottom' | 'right-top' | 'top-left' | 'top-right';

type kebabMenuType = {
  options: optionType[];
  stopPropagation: boolean;
  direction?: directionType;
  data: {};
  pid: string | number;
  openedModalId: string | number;
  onDropdownOpen: () => void;
};

function getPosition(direction: directionType) {
  switch (direction) {
    case 'left-top':
      return 'fmtm-top-[2px] fmtm-right-[40px]';
    case 'left-bottom':
      return 'fmtm-top-[40px] fmtm-right-[0px]';
    case 'right-bottom':
      return 'fmtm-top-[40px] fmtm-left-[0px]';
    case 'right-top':
      return 'fmtm-top-[2px] fmtm-left-[40px]';
    case 'top-left':
      return 'fmtm-bottom-[40px] fmtm-right-[0px]';
    case 'top-right':
      return 'fmtm-bottom-[40px] fmtm-left-[0px]';
    default:
      return 'fmtm-top-[2px] fmtm-right-[40px]';
  }
}

function KebabMenu({
  options,
  stopPropagation,
  direction = 'left-bottom',
  data,
  pid,
  openedModalId,
  onDropdownOpen,
}: kebabMenuType) {
  const [toggle, handleToggle] = useState(false);
  const toggleRef = useRef(null);
  const nodeRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLInputElement>(null);
  const [position, setPosition] = useState(direction);

  useLayoutEffect(() => {
    if (!toggle || !dropdownRef?.current) return;
    const { bottom } = dropdownRef?.current?.getBoundingClientRect();
    const { height } = nodeRef?.current?.getBoundingClientRect() || { height: 0 };
    const windowHeight = window.innerHeight;
    if (bottom + height > windowHeight) {
      setPosition('top-left');
    } else {
      setPosition('left-bottom');
    }
  }, [toggle]);

  const onOutsideClick = useCallback(
    (e) => {
      if (nodeRef.current && !nodeRef.current.contains(e.target)) {
        handleToggle(false);
      }
    },
    [nodeRef, handleToggle],
  );

  useEffect(() => {
    if (toggle) {
      window.addEventListener('click', onOutsideClick);
    } else {
      window.removeEventListener('click', onOutsideClick);
    }
  }, [toggle, onOutsideClick]);

  useEffect(() => {
    if (pid !== openedModalId && toggle) {
      handleToggle(false);
    }
  }, [pid, openedModalId]);

  return (
    <div className="fmtm-relative fmtm-w-10 fmtm-flex fmtm-justify-end" ref={dropdownRef}>
      <a
        ref={toggleRef}
        className="fmtm-inline-flex fmtm-items-center fmtm-text-sm fmtm-font-medium 
       fmtm-text-grey-800 fmtm-rounded-full hover:fmtm-bg-grey-100 focus:fmtm-ring-4 
       focus:fmtm-outline-none focus:ring-grey-50 fmtm-select-none hover:fmtm-duration-300"
        onClick={(e) => {
          e.preventDefault();
          if (stopPropagation) e.stopPropagation();
          handleToggle(!toggle);
          onDropdownOpen();
        }}
      >
        <button type="button" className="fmtm-text-icon-md fmtm-flex fmtm-p-1">
          <AssetModules.MoreVertIcon />
        </button>
      </a>
      <div
        ref={nodeRef}
        className={`
        ${pid === openedModalId && toggle ? '' : 'fmtm-hidden'} 
        fmtm-absolute ${getPosition(position)} fmtm-z-[1000]
        fmtm-bg-white fmtm-rounded-lg fmtm-divide-y fmtm-divide-grey-100
        fmtm-shadow-3xl fmtm-shadow-lg`}
      >
        <ul
          className="fmtm-py-0 fmtm-text-sm fmtm-text-grey-700 pm-dropdown_menu mt-2"
          aria-labelledby="dropdownMenuIconButton"
        >
          {options.map(({ id, label, onClick, icon }: optionType) => (
            <li
              role="presentation"
              key={id}
              className="fmtm-py-2 fmtm-px-2 hover:fmtm-bg-[#F2E3E3] fmtm-cursor-pointer fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-duration-300"
              onClick={(e) => {
                e.preventDefault();
                if (stopPropagation) e.stopPropagation();
                onClick(data);
              }}
            >
              {icon && <div>{icon}</div>}
              <p className="fmtm-text-[#484848] fmtm-text-sm">{label}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default KebabMenu;
