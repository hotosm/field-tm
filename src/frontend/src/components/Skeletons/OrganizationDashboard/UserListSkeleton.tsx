import React from 'react';
import { Skeleton } from '@/components/Skeletons';

const UserListSkeleton = () => {
  return (
    <div className="fmtm-flex fmtm-items-center">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton
          key={i}
          style={{ zIndex: 5 - i }}
          className="fmtm-border !fmtm-rounded-full fmtm-h-[1.688rem] fmtm-w-[1.688rem] fmtm-mr-[-0.5rem]"
        />
      ))}
      <Skeleton className="fmtm-w-[2rem] fmtm-h-[1rem] fmtm-ml-4" />
    </div>
  );
};

export default UserListSkeleton;
