import React from 'react';
import CoreModules from '@/shared/CoreModules';

const ProjectInfoSkeleton = () => {
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

export default ProjectInfoSkeleton;
