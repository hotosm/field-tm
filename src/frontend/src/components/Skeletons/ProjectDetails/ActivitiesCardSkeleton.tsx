import React from 'react';
import CoreModules from '@/shared/CoreModules';

const ActivitiesCardSkeleton = () => {
  return (
    <div className="fmtm-flex fmtm-items-center fmtm-justify-between fmtm-border-b-[1px] fmtm-border-white fmtm-py-3 fmtm-pr-1">
      <CoreModules.Skeleton className="!fmtm-w-[2.81rem] fmtm-h-[2.81rem] !fmtm-rounded-full fmtm-overflow-hidden" />
      <div className="fmtm-w-[70%]">
        <CoreModules.Skeleton />
        <CoreModules.Skeleton className="!fmtm-w-[50%]" />
        <div className="fmtm-flex fmtm-justify-between !fmtm-w-full">
          <div className="fmtm-w-[25%]">
            <CoreModules.Skeleton />
          </div>
          <div className="fmtm-w-[70%]">
            <CoreModules.Skeleton />
          </div>
        </div>
      </div>
      <CoreModules.Skeleton className="!fmtm-w-5 fmtm-h-5" />
    </div>
  );
};

export default ActivitiesCardSkeleton;
