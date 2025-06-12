import React from 'react';
import { Skeleton } from '@/components/Skeletons';

// Skeleton card main purpose is to perform loading in case of any delay in retrieving project
const ProjectCardSkeleton = ({ className }: { className?: string }) => {
  return Array.from({ length: 12 }).map((_, i) => (
    <div
      key={i}
      className={`fmtm-h-[15.5rem] fmtm-bg-white fmtm-rounded-lg fmtm-p-4 fmtm-flex fmtm-flex-col fmtm-justify-between ${className}`}
    >
      <div>
        <Skeleton className="fmtm-w-8 fmtm-h-8 !fmtm-rounded-full" />
        <div className="fmtm-my-3">
          <Skeleton className="fmtm-w-8 fmtm-h-[14px] !fmtm-rounded-full fmtm-mb-1" />
          <Skeleton className="fmtm-w-[80px] fmtm-h-[14px] !fmtm-rounded-full" />
        </div>
        <Skeleton className="fmtm-w-14 fmtm-h-[14px] !fmtm-rounded-full fmtm-mb-1" />
        <Skeleton className="fmtm-w-full fmtm-h-[14px] !fmtm-rounded-full" />
        <Skeleton className="fmtm-w-full fmtm-h-[14px] !fmtm-rounded-full fmtm-my-1" />
        <Skeleton className="fmtm-w-[50%] fmtm-h-[14px] !fmtm-rounded-full" />
      </div>

      <div>
        <div className="fmtm-flex fmtm-items-center fmtm-justify-between fmtm-mb-1">
          <Skeleton className="fmtm-w-10 fmtm-h-[14px] !fmtm-rounded-full" />
          <Skeleton className="fmtm-w-16 fmtm-h-[14px] !fmtm-rounded-full" />
        </div>
        <Skeleton className="fmtm-w-full fmtm-h-[6px] !fmtm-rounded-full" />
      </div>
    </div>
  ));
};
export default ProjectCardSkeleton;
