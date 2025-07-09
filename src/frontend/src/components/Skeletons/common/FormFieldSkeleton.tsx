import React from 'react';
import { Skeleton } from '..';

type props = {
  count?: number;
};

const FormFieldSkeletonLoader = ({ count = 10 }: props) => (
  <div className="fmtm-flex fmtm-flex-col fmtm-gap-6">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i}>
        <Skeleton className="fmtm-h-[1.75rem] fmtm-w-[10rem] fmtm-mb-2" />
        <Skeleton className="fmtm-h-[2.75rem] fmtm-w-full" />
      </div>
    ))}
  </div>
);

export default FormFieldSkeletonLoader;
