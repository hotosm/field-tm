import React from 'react';
import CoreModules from '../../shared/CoreModules';

const ProjectInfoCountCardSkeleton = () => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'auto auto auto',
        gap: '20px',
      }}
    >
      {Array.from({ length: 3 }).map((i) => (
        <div id={i}>
          <CoreModules.Skeleton sx={{ bgcolor: 'grey.900' }} variant="rectangular" width={250} height={128} />
        </div>
      ))}
    </div>
  );
};

export default ProjectInfoCountCardSkeleton;
