import React, { useEffect, useState } from 'react';
import AssetModules from '@/shared/AssetModules';

interface IAccordion {
  collapsed?: boolean;
  header: any;
  body: any;
  className?: string;
  onToggle: any;
  description?: string;
  disableHeaderClickToggle?: boolean;
}

export default function Accordion({
  collapsed: isCollapsed,
  header,
  body,
  className,
  onToggle,
  description,
  disableHeaderClickToggle,
}: IAccordion) {
  const [collapsed, setCollapsed] = useState(isCollapsed);

  useEffect(() => {
    setCollapsed(isCollapsed);
  }, [isCollapsed]);

  return (
    <div className={`fmtm-bg-white fmtm-p-2 fmtm-pb-3 ${className} `}>
      <div className="">
        <div
          className={`fmtm-flex fmtm-items-center fmtm-justify-between
            fmtm-w-full fmtm-font-bold fmtm-gap-3 fmtm-cursor-pointer fmtm-text-2xl fmtm-py-2  fmtm-border-[#929DB3] ${
              collapsed ? 'fmtm-border-b-[0px]' : 'fmtm-border-b-[2px]'
            }`}
          onClick={() => {
            if (disableHeaderClickToggle) return;
            setCollapsed(!collapsed);
            onToggle(collapsed);
          }}
        >
          {header}
          <span className="fmtm-flex fmtm-w-9 fmtm-h-9">
            <button
              type="button"
              title={collapsed ? 'Expand' : 'Collapse'}
              className={`fmtm-rounded-lg fmtm-p-1.5 fmtm-flex fmtm-items-center ${
                !collapsed ? '' : 'hover:fmtm-bg-grey-10'
              }`}
              onClick={() => {
                setCollapsed(!collapsed);
                onToggle(collapsed);
              }}
            >
              <AssetModules.ArrowRightIcon
                color=""
                style={{ fontSize: 32 }}
                className={`${collapsed ? '' : 'fmtm-rotate-90'}`}
              />
            </button>
          </span>
        </div>
        <div className="fmtm-bg-red-600">{description}</div>
      </div>
      <div className={`${collapsed ? 'fmtm-hidden' : ''}`}>{body}</div>
    </div>
  );
}
