import React from 'react';
import CoreModules from '@/shared/CoreModules';

const TaskCardSkeleton = () => {
  return (
    <div className="fmtm-bg-red-50 fmtm-px-5 fmtm-pb-5 fmtm-pt-2 fmtm-rounded-lg">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-1">
        <CoreModules.Skeleton className="!fmtm-w-[100px]" />
        <div className="fmtm-flex fmtm-justify-between">
          <CoreModules.Skeleton className="!fmtm-w-[125px]" />
          <CoreModules.Skeleton className="!fmtm-w-[30px]" />
        </div>
        <div className="fmtm-flex fmtm-justify-between">
          <CoreModules.Skeleton className="!fmtm-w-[140px]" />
          <CoreModules.Skeleton className="!fmtm-w-[30px]" />
        </div>
      </div>
      <div className="fmtm-flex fmtm-justify-between fmtm-flex-col sm:fmtm-flex-row fmtm-gap-2 fmtm-mt-3">
        <CoreModules.Skeleton className="!fmtm-w-[145px] fmtm-h-8" />
        <CoreModules.Skeleton className="!fmtm-w-[145px] fmtm-h-8" />
      </div>
    </div>
  );
};

export default TaskCardSkeleton;
