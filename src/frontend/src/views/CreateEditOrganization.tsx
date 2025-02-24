import React, { useEffect } from 'react';
import CoreModules from '@/shared/CoreModules';
import CreateEditOrganizationHeader from '@/components/CreateEditOrganization/CreateEditOrganizationHeader';
import ConsentDetailsForm from '@/components/CreateEditOrganization/ConsentDetailsForm';
import CreateEditOrganizationForm from '@/components/CreateEditOrganization/CreateEditOrganizationForm';
import { OrganisationAction } from '@/store/slices/organisationSlice';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { useHasManagedAnyOrganization, useIsAdmin, useIsOrganizationAdmin } from '@/hooks/usePermissions';
import NoAccessComponent from '@/views/NoAccessComponent';

const CreateEditOrganization = () => {
  const params = CoreModules.useParams();
  const dispatch = useAppDispatch();
  const organizationId: string = params.id;
  const isAdmin = useIsAdmin();
  const isOrganizationAdmin = useIsOrganizationAdmin(+organizationId);
  const hasManagedAnyOrganization = useHasManagedAnyOrganization();

  if ((organizationId && !isOrganizationAdmin) || (!organizationId && hasManagedAnyOrganization && !isAdmin))
    return <NoAccessComponent />;

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
    <div className="fmtm-bg-[#F5F5F5]">
      <CreateEditOrganizationHeader organizationId={organizationId} />
      <div className="fmtm-box-border fmtm-pt-4">
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
