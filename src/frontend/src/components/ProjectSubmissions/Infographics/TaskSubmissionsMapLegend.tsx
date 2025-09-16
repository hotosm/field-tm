import { legendColorArrayType } from '@/models/task/taskModel';
import React from 'react';

const LegendListItem = ({ code }) => (
  <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
    <div style={{ backgroundColor: code.color }} className="fmtm-w-10 fmtm-h-6 fmtm-mx-2"></div>
    <div>
      {code.min !== code.max ? (
        <p>
          {code.min} - {code.max}
        </p>
      ) : (
        <p>{code.min}</p>
      )}
    </div>
  </div>
);

const TaskSubmissionsMapLegend = ({ legendColorArray }: { legendColorArray: legendColorArrayType[] }) => {
  return (
    <div className="fmtm-py-3">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-2 sm:fmtm-gap-4">
        {legendColorArray?.reverse()?.map((code) => (
          <LegendListItem key={code.color} code={code} />
        ))}
      </div>
    </div>
  );
};

export default TaskSubmissionsMapLegend;
