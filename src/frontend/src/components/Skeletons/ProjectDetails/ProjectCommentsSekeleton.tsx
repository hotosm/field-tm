import React from 'react';
import CoreModules from '@/shared/CoreModules';

const ProjectCommentsSekeleton = () => {
  return (
    <div className="fmtm-flex fmtm-gap-4 fmtm-px-2">
      <CoreModules.Skeleton style={{ width: '32px', height: '32px' }} className="!fmtm-rounded-full" />
      <div className="fmtm-flex-1">
        <div className="fmtm-flex fmtm-gap-4 fmtm-mt-2">
          <CoreModules.Skeleton style={{ width: '80px' }} />
          <CoreModules.Skeleton style={{ width: '150px' }} />
        </div>
        <CoreModules.Skeleton style={{ width: '100%', height: '100px' }} />
      </div>
    </div>
  );
};

export default ProjectCommentsSekeleton;
