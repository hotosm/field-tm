import React from 'react';

const colorCodes = [
  { color: '#0062AC', min: 130, max: 160 },
  { color: '#4A90D9', min: 100, max: 130 },
  { color: '#7CB2E8', min: 50, max: 100 },
  { color: '#A9D2F3', min: 10, max: 50 },
  { color: '#FF4538', min: 0, max: 0 },
];

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

const ProjectInfoMapLegend = () => {
  return (
    <div className="fmtm-py-3">
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-2 sm:fmtm-gap-4">
        {colorCodes.map((code) => (
          <LegendListItem key={code.color} code={code} />
        ))}
      </div>
    </div>
  );
};

export default ProjectInfoMapLegend;
