import React from 'react';
import ProjectDeleteTab from './ProjectDeleteTab';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';

const EditTab = ({ projectId, projectName }) => {
  useDocumentTitle('Manage Project: Delete Project');
  return (
    <div className="fmtm-max-w-[29.5rem]">
      <ProjectDeleteTab projectId={projectId} projectName={projectName} />
    </div>
  );
};

export default EditTab;
