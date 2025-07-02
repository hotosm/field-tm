import React from 'react';
import CoreModules from '@/shared/CoreModules';

const ShowingCountSkeleton = () => {
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

export default ShowingCountSkeleton;
