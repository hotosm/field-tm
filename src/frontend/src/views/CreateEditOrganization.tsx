import React from 'react';
import CoreModules from '@/shared/CoreModules';
import environment from '@/environment';
import CreateEditOrganizationHeader from '@/components/CreateEditOrganization/CreateEditOrganizationHeader';
import ConsentDetailsForm from '@/components/CreateEditOrganization/ConsentDetailsForm';
import CreateEditOrganizationForm from '@/components/CreateEditOrganization/CreateEditOrganizationForm';

const CreateEditOrganization = () => {
  const params = CoreModules.useParams();
  const organizationId = params.id;
  const consentApproval: any = CoreModules.useAppSelector((state) => state.organisation.consentApproval);

  return (
    <div className="fmtm-bg-[#F5F5F5]">
      <CreateEditOrganizationHeader organizationId={organizationId} />
      <div className="fmtm-box-border fmtm-border-[1px] fmtm-border-t-white fmtm-border-t-[0px] fmtm-px-5 fmtm-py-4">
        {organizationId || (!organizationId && consentApproval) ? (
          <CreateEditOrganizationForm organizationId={organizationId} />
        ) : (
          <ConsentDetailsForm />
        )}
      </div>
    </div>
  );
};

export default CreateEditOrganization;
