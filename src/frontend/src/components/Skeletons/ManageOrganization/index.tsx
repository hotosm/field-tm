import React from 'react';
import { Skeleton } from '..';
import FormFieldSkeletonLoader from '@/components/Skeletons/common/FormFieldSkeleton';

const ManageOrganizationSkeleton = () => {
  return (
    <div className="sm:fmtm-flex-1 fmtm-flex fmtm-justify-center fmtm-flex-col sm:fmtm-flex-row fmtm-gap-5 sm:fmtm-overflow-hidden">
      {/* left container */}
      <div className="fmtm-bg-white fmtm-h-full fmtm-rounded-xl sm:fmtm-w-[17.5rem] fmtm-p-6 fmtm-flex sm:fmtm-flex-col fmtm-flex-wrap sm:fmtm-flex-nowrap fmtm-gap-x-5">
        <div className="fmtm-flex fmtm-flex-col fmtm-items-center fmtm-mx-auto fmtm-gap-3 fmtm-mb-2 sm:fmtm-mb-6">
          <Skeleton className="fmtm-w-[4.688rem] fmtm-h-[4.688rem] !fmtm-rounded-full" />
          <Skeleton className="fmtm-w-[6.5rem] fmtm-h-[1.25rem]" />
        </div>
        <Skeleton className="fmtm-w-full fmtm-h-[3rem] fmtm-mb-1" />
        <Skeleton className="fmtm-w-full fmtm-h-[3rem]" />
        <Skeleton className="fmtm-w-full fmtm-h-[3rem] fmtm-mt-auto" />
      </div>

      {/* right container */}
      <div className="fmtm-bg-white fmtm-h-full fmtm-rounded-xl fmtm-w-full fmtm-max-w-[54rem] sm:fmtm-overflow-y-scroll sm:scrollbar fmtm-py-10 fmtm-px-9">
        <FormFieldSkeletonLoader count={5} />
      </div>
    </div>
  );
};

export default ManageOrganizationSkeleton;
