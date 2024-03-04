import React, { useEffect, useState } from 'react';
import ProjectDescriptionTab from './ProjectDescriptionTab';
import FormUpdateTab from './FormUpdateTab';

const tabList: ['Project Description', 'Form Update'] = ['Project Description', 'Form Update'];

const EditTab = ({ projectId }) => {
  const [tabView, setTabView] = useState<'Project Description' | 'Form Update'>('Project Description');

  return (
    <div>
      <div className="fmtm-flex fmtm-gap-3 fmtm-mb-5">
        {tabList.map((tab) => (
          <div
            key={tab}
            className={`fmtm-w-fit fmtm-text-[#9B9999] fmtm-px-2 fmtm-border-b-[1px] hover:fmtm-border-primaryRed fmtm-duration-300 fmtm-cursor-pointer ${
              tabView === tab ? 'fmtm-border-primaryRed' : 'fmtm-border-transparent'
            }`}
            onClick={() => setTabView(tab)}
          >
            {tab}
          </div>
        ))}
      </div>
      <div>
        {tabView === 'Project Description' ? (
          <div className="fmtm-max-w-[42rem]">
            <ProjectDescriptionTab projectId={projectId} />
          </div>
        ) : (
          <div className="fmtm-max-w-[29.5rem]">
            <FormUpdateTab projectId={projectId} />
          </div>
        )}
      </div>
    </div>
  );
};

export default EditTab;
