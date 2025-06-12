import React from 'react';
import { Skeleton } from '@/components/Skeletons';
import UserListSkeleton from './UserListSkeleton';

const OrganizationInfoSkeleton = () => {
  return (
    <div className="fmtm-flex fmtm-justify-between fmtm-flex-wrap sm:fmtm-flex-nowrap fmtm-gap-x-8 fmtm-gap-y-2 fmtm-bg-white fmtm-rounded-lg fmtm-p-4">
      <div className="fmtm-flex fmtm-gap-x-6">
        <Skeleton className="fmtm-w-[4.688rem] fmtm-h-[4.688rem] !fmtm-rounded-full" />
        <div className="xl:fmtm-w-[39rem] xl:fmtm-max-w-[39rem]">
          <Skeleton className="fmtm-w-[8rem] fmtm-h-[34px] fmtm-mb-2" />
          <Skeleton className="fmtm-w-[15rem] fmtm-h-[20px]" />
        </div>
      </div>

      <div className="fmtm-flex fmtm-flex-col fmtm-gap-y-3">
        <div>
          <Skeleton className="fmtm-w-[11rem] fmtm-h-[1rem] fmtm-mb-1" />
          <div className="fmtm-flex fmtm-items-center">
            <UserListSkeleton />
          </div>
        </div>
        <Skeleton className="fmtm-w-[11rem] fmtm-h-[1rem]" />
        <Skeleton className="fmtm-w-[11rem] fmtm-h-[1rem]" />
      </div>
      <div className="fmtm-my-auto">
        <Skeleton className="fmtm-w-[10rem] fmtm-h-[2.5rem]" />
      </div>
    </div>
  );
};

export default OrganizationInfoSkeleton;
