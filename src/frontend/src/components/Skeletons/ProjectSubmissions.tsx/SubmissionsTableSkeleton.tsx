import React from 'react';
import CoreModules from '@/shared/CoreModules';

const SubmissionsTableSkeleton = () => {
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

export default SubmissionsTableSkeleton;
