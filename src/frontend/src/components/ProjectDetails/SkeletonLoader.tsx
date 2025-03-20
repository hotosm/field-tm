import React from 'react';
import CoreModules from '@/shared/CoreModules';

export const ProjectInfoSkeletonLoader = () => {
  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-5">
      <div>
        <CoreModules.Skeleton width={70} height={14} />
        <CoreModules.Skeleton height={14} count={7} />
        <CoreModules.Skeleton width={70} height={14} />
      </div>
      <div>
        <CoreModules.Skeleton width={90} height={14} />
        <CoreModules.Skeleton width={20} height={14} />
      </div>
      <div>
        <CoreModules.Skeleton width={100} height={14} />
        <CoreModules.Skeleton width={120} height={14} />
      </div>
      <div>
        <CoreModules.Skeleton width={140} height={14} />
        <CoreModules.Skeleton width={120} height={14} />
      </div>
      <div>
        <CoreModules.Skeleton width={110} height={14} />
        <CoreModules.Skeleton width={42} height={42} className="!fmtm-rounded-full" />
      </div>
      <div>
        <CoreModules.Skeleton width={150} height={14} />
        <CoreModules.Skeleton height={6} className="!fmtm-rounded-xl" />
      </div>
    </div>
  );
};

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
