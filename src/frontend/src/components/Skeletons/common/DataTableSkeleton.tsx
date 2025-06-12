import React from 'react';
import CoreModules from '@/shared/CoreModules';

export default function TableSkeleton() {
  return (
    <div className="fmtm-overflow-x-scroll scrollbar fmtm-bg-white fmtm-px-5 fmtm-mt-3 fmtm-rounded-lg">
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className={`fmtm-grid fmtm-grid-cols-6 fmtm-gap-1 sm:fmtm-gap-10 fmtm-py-[6px]`}>
          {Array.from({ length: 6 }).map((_, ind) => (
            <CoreModules.Skeleton className="fmtm-h-6" baseColor={`${i === 0 ? '#cfcfcf' : ''}`} key={ind} />
          ))}
        </div>
      ))}
    </div>
  );
}
