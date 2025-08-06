import React from 'react';
import OrganizationInfo from '@/components/OrganizationDashboard/OrganizationInfo';
import ProjectSummary from '@/components/OrganizationDashboard/ProjectSummary';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';

const OrganizationDashboard = () => {
  useDocumentTitle('Organization Dashboard');

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-5 fmtm-h-full">
      <OrganizationInfo />
      <ProjectSummary />
    </div>
  );
};

export default OrganizationDashboard;
