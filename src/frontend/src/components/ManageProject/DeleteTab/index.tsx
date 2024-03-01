import React from 'react';
import ProjectDeleteTab from './ProjectDeleteTab';

const EditTab = ({ projectId, projectName }) => {
  return (
    <div className="fmtm-max-w-[29.5rem]">
      <ProjectDeleteTab projectId={projectId} projectName={projectName} />
    </div>
  );
};

export default EditTab;
