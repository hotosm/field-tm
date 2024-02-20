import React, { useEffect } from 'react';
import CoreModules from '@/shared/CoreModules';
import CreateEditOrganizationHeader from '@/components/CreateEditOrganization/CreateEditOrganizationHeader';
import ConsentDetailsForm from '@/components/CreateEditOrganization/ConsentDetailsForm';
import CreateEditOrganizationForm from '@/components/CreateEditOrganization/CreateEditOrganizationForm';
import { useDispatch } from 'react-redux';
import { OrganisationAction } from '@/store/slices/organisationSlice';

const CreateEditOrganization = () => {
  const params = CoreModules.useParams();
  const dispatch = useDispatch();
  const organizationId = params.id;
  const consentApproval: any = CoreModules.useAppSelector((state) => state.organisation.consentApproval);

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
