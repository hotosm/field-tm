import React from 'react';
import CoreModules from '@/shared/CoreModules';

export const TaskCardSkeletonLoader = () => {
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

export const SubmissionsTableSkeletonLoader = () => {
  return (
    <div className="fmtm-overflow-x-scroll scrollbar fmtm-bg-white fmtm-px-5 fmtm-mt-3">
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className={`fmtm-flex fmtm-gap-10 fmtm-py-[6px]`}>
          <CoreModules.Skeleton baseColor={`${i === 0 ? '#cfcfcf' : ''}`} className={`!fmtm-w-[50px]`} />
          {Array.from({ length: 15 }).map((_, ind) => (
            <CoreModules.Skeleton baseColor={`${i === 0 ? '#cfcfcf' : ''}`} key={ind} className={`!fmtm-w-[100px]`} />
          ))}
        </div>
      ))}
    </div>
  );
};
