import React, { useEffect, useState } from 'react';
import environment from '@/environment';
import ProjectDescriptionTab from './ProjectDescriptionTab';
import FormUpdateTab from './FormUpdateTab';
import { FormCategoryService, GetIndividualProjectDetails } from '@/api/CreateProjectService';
import CoreModules from '@/shared/CoreModules';

const tabList: ['Project Description', 'Form Update'] = ['Project Description', 'Form Update'];

const EditTab = ({ projectId }) => {
  const dispatch = CoreModules.useAppDispatch();
  const [tabView, setTabView] = useState<'Project Description' | 'Form Update'>('Project Description');

  useEffect(() => {
    dispatch(FormCategoryService(`${import.meta.env.VITE_API_URL}/central/list-forms`));
  }, []);

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
      <div className="fmtm-max-w-[29.5rem]">
        {tabView === 'Project Description' ? (
          <ProjectDescriptionTab projectId={projectId} />
        ) : (
          <FormUpdateTab projectId={projectId} />
        )}
      </div>
    </div>
  );
};

export default EditTab;
