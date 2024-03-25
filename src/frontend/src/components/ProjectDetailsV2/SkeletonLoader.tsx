import React from 'react';
import CoreModules from '@/shared/CoreModules';

export const ActivitiesCardSkeletonLoader = () => {
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

export const ShowingCountSkeletonLoader = () => {
  return (
    <div className="fmtm-flex fmtm-gap-2 fmtm-pt-2">
      <CoreModules.Skeleton style={{ width: '80px' }} />
      <CoreModules.Skeleton style={{ width: '20px' }} />
      <CoreModules.Skeleton style={{ width: '25px' }} />
      <CoreModules.Skeleton style={{ width: '20px' }} />
      <CoreModules.Skeleton style={{ width: '70px' }} />
    </div>
  );
};

export const ProjectCommentsSekeletonLoader = () => {
  return (
    <div className="fmtm-flex fmtm-gap-4 fmtm-px-2">
      <CoreModules.Skeleton style={{ width: '32px', height: '32px' }} className="!fmtm-rounded-full" />
      <div className="fmtm-flex-1">
        <div className="fmtm-flex fmtm-gap-4 fmtm-mt-2">
          <CoreModules.Skeleton style={{ width: '80px' }} />
          <CoreModules.Skeleton style={{ width: '150px' }} />
        </div>
        <CoreModules.Skeleton style={{ width: '100%', height: '100px' }} />
      </div>
    </div>
  );
};
