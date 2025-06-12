import React from 'react';
import { Skeleton } from '..';

const OrganizationCardSkeleton = () => {
  return (
    <div className="fmtm-w-full fmtm-h-[10.375rem] fmtm-flex fmtm-gap-4 fmtm-p-5 fmtm-bg-white">
      <Skeleton className="fmtm-w-[7.5rem] fmtm-h-[7.5rem] !fmtm-rounded-full" />
      <div className="">
        <Skeleton className="fmtm-w-[7.5rem] fmtm-h-[1.75rem] fmtm-mb-2" />
        <Skeleton className="fmtm-w-[7.5rem] fmtm-h-[1.5rem]" />
      </div>
    </div>
  );
};

export default OrganizationCardSkeleton;
