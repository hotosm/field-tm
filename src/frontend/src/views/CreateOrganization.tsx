import React, { useEffect } from 'react';
import CreateEditOrganizationHeader from '@/components/CreateEditOrganization/CreateEditOrganizationHeader';
import ConsentDetailsForm from '@/components/CreateEditOrganization/ConsentDetailsForm';
import CreateEditOrganizationForm from '@/components/CreateEditOrganization/CreateEditOrganizationForm';
import { OrganisationAction } from '@/store/slices/organisationSlice';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { useHasManagedAnyOrganization, useIsAdmin } from '@/hooks/usePermissions';
import Forbidden from '@/views/Forbidden';
import InstructionsSidebar from '@/components/CreateEditOrganization/InstructionsSidebar';

const CreateOrganization = () => {
  const dispatch = useAppDispatch();
  const isAdmin = useIsAdmin();
  const hasManagedAnyOrganization = useHasManagedAnyOrganization();

  if (hasManagedAnyOrganization && !isAdmin) return <Forbidden />;

  const consentApproval = useAppSelector((state) => state.organisation.consentApproval);

  useEffect(() => {
    // clear consent form on new org add
    dispatch(
      OrganisationAction.SetConsentDetailsFormData({
        give_consent: '',
        review_documentation: [],
        log_into: [],
        participated_in: [],
      }),
    );
    dispatch(OrganisationAction.SetConsentApproval(false));
  }, []);

  useEffect(() => {
    // clear state of formData to empty
    dispatch(OrganisationAction.SetOrganisationFormData({}));
  }, []);

  return (
    <div className="fmtm-h-full lg:fmtm-overflow-hidden">
      <CreateEditOrganizationHeader organizationId={''} />
      <div className="fmtm-box-border fmtm-pt-4 lg:fmtm-h-[calc(100%-42.5px)]">
        {consentApproval ? (
          <div className={`fmtm-flex fmtm-flex-col lg:fmtm-flex-row fmtm-gap-5 lg:fmtm-gap-10 fmtm-pt-4 fmtm-h-full`}>
            <InstructionsSidebar />
            <div className="fmtm-w-full fmtm-h-full xl:fmtm-max-w-[50rem] fmtm-bg-white">
              <CreateEditOrganizationForm organizationId={''} />
            </div>
          </div>
        ) : (
          <ConsentDetailsForm />
        )}
      </div>
    </div>
  );
};

export default CreateOrganization;
