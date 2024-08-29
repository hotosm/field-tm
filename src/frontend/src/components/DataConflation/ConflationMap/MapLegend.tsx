import React from 'react';
import Accordion from '@/components/common/Accordion';
import useOutsideClick from '@/hooks/useOutsideClick';

const legendArray = [
  { name: 'No conflicts', color: '#40AC8C' },
  { name: 'Tag conflicts', color: '#DB9D35' },
  { name: 'Geometry conflicts', color: '#3C4A5E' },
  { name: 'Both conflicts', color: '#EB8B8B' },
];

const MapLegends = () => {
  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-1 fmtm-pb-2">
      {legendArray?.map((legend) => (
        <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
          <div
            style={{ backgroundColor: legend.color }}
            className={`fmtm-w-[0.875rem] fmtm-h-[0.875rem] fmtm-min-w-[0.875rem] fmtm-min-h-[0.875rem]`}
          ></div>
          <p className="fmtm-text-xs fmtm-text-[#484848]">{legend.name}</p>
        </div>
      ))}
    </div>
  );
};

const MapLegend = () => {
  const [legendRef, legendToggle, handleLegendToggle] = useOutsideClick();

  return (
    <>
      <Accordion
        hasSeperator={false}
        ref={legendRef}
        body={<MapLegends />}
        header={
          <div className="fmtm-flex fmtm-items-center fmtm-gap-1 sm:fmtm-gap-2">
            <p className="fmtm-text-base fmtm-font-bold">Legend</p>
          </div>
        }
        onToggle={() => {
          handleLegendToggle();
        }}
        className="fmtm-py-0 !fmtm-pb-0 fmtm-rounded-lg hover:fmtm-bg-gray-50"
        collapsed={!legendToggle}
      />
    </>
  );
};

export default MapLegend;
