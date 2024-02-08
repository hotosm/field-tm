import React, { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import InputTextField from '@/components/common/InputTextField';
import TextArea from '@/components/common/TextArea';
import Button from '@/components/common/Button';
import { ApproveOrganizationService, GetIndividualOrganizationService } from '@/api/OrganisationService';
import CoreModules from '@/shared/CoreModules';

const OrganizationForm = () => {
  const dispatch = useDispatch();
  const params = useParams();
  const organizationId = params.id;
  const organisationFormData: any = CoreModules.useAppSelector((state) => state.organisation.organisationFormData);

  useEffect(() => {
    if (organizationId) {
      dispatch(GetIndividualOrganizationService(`${import.meta.env.VITE_API_URL}/organisation/${organizationId}`));
    }
  }, [organizationId]);

  const approveOrganization = () => {
    dispatch(
      ApproveOrganizationService(`${import.meta.env.VITE_API_URL}/organisation/approve`, { org_id: organizationId }),
    );
  };

  return (
    <div className="fmtm-max-w-[50rem] fmtm-bg-white fmtm-py-5 lg:fmtm-py-10 fmtm-px-5 lg:fmtm-px-9 fmtm-mx-auto">
      <div className="fmtm-flex fmtm-justify-center">
        <h5 className="fmtm-text-[#484848] fmtm-text-2xl fmtm-font-[600] fmtm-pb-3 lg:fmtm-pb-7 fmtm-font-archivo fmtm-tracking-wide">
          Organizational Details
        </h5>
      </div>
      <div className="fmtm-flex fmtm-flex-col fmtm-gap-6">
        <InputTextField
          id="name"
          name="name"
          label="Community or Organization Name"
          value={organisationFormData?.name}
          onChange={() => {}}
          fieldType="text"
        />
        <InputTextField
          id="email"
          name="email"
          label="Email"
          value={organisationFormData?.email}
          onChange={() => {}}
          fieldType="text"
        />
        <InputTextField
          id="url"
          name="url"
          label="Website URL"
          value={organisationFormData?.url}
          onChange={() => {}}
          fieldType="text"
        />
        <TextArea
          id="description"
          name="description"
          label="Description"
          rows={3}
          value={organisationFormData?.description}
          onChange={() => {}}
        />
        <InputTextField
          id="odk_central_url"
          name="odk_central_url"
          label="ODK Central URL "
          value={organisationFormData?.odk_central_url}
          onChange={() => {}}
          fieldType="text"
        />
        <InputTextField
          id="url"
          name="url"
          label="Community or Organization are you applied for? "
          value={organisationFormData?.organization_type}
          onChange={() => {}}
          fieldType="text"
        />
        <div>
          <p className="fmtm-text-[1rem] fmtm-font-semibold fmtm-mb-2">Logo</p>
          {organisationFormData?.logo ? (
            <div>
              <img
                src={organisationFormData?.logo}
                alt=""
                className="fmtm-h-[100px] fmtm-rounded-sm fmtm-border-[1px]"
              />
            </div>
          ) : (
            <p className="fmtm-ml-3">-</p>
          )}
        </div>
      </div>
      <div className="fmtm-flex fmtm-items-center fmtm-justify-center fmtm-gap-6 fmtm-mt-8 lg:fmtm-mt-16">
        <Button btnText="Reject" btnType="other" className="fmtm-font-bold" onClick={() => {}} />
        <Button btnText="Verify" btnType="primary" className="fmtm-font-bold" onClick={approveOrganization} />
      </div>
    </div>
  );
};

export default OrganizationForm;
