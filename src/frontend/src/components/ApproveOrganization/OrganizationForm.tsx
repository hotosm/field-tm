import React, { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate, useParams } from 'react-router-dom';
import InputTextField from '@/components/common/InputTextField';
import TextArea from '@/components/common/TextArea';
import Button from '@/components/common/Button';
import {
  ApproveOrganizationService,
  GetIndividualOrganizationService,
  RejectOrganizationService,
} from '@/api/OrganisationService';
import { OrganisationAction } from '@/store/slices/organisationSlice';
import { useAppSelector } from '@/types/reduxTypes';

const OrganizationForm = () => {
  const dispatch = useDispatch();
  const params = useParams();
  const navigate = useNavigate();
  const organizationId = params.id;
  const organisationFormData = useAppSelector((state) => state.organisation.organisationFormData);
  const organizationApproving = useAppSelector(
    (state) => state.organisation.organizationApprovalStatus.organizationApproving,
  );
  const organizationRejecting = useAppSelector(
    (state) => state.organisation.organizationApprovalStatus.organizationRejecting,
  );
  const organizationApprovalSuccess = useAppSelector(
    (state) => state.organisation.organizationApprovalStatus.isSuccess,
  );

  useEffect(() => {
    if (organizationId) {
      dispatch(GetIndividualOrganizationService(`${import.meta.env.VITE_API_URL}/organisation/${organizationId}`));
    }
  }, [organizationId]);

  const approveOrganization = () => {
    if (organizationId) {
      dispatch(
        ApproveOrganizationService(
          `${import.meta.env.VITE_API_URL}/organisation/approve?org_id=${parseInt(organizationId)}`,
        ),
      );
    }
  };

  const rejectOrganization = () => {
    dispatch(RejectOrganizationService(`${import.meta.env.VITE_API_URL}/organisation/unapproved/${organizationId}`));
  };

  // redirect to manage-organization page after approve/reject success
  useEffect(() => {
    if (organizationApprovalSuccess) {
      dispatch(OrganisationAction.SetOrganisationFormData({}));
      dispatch(OrganisationAction.SetOrganizationApprovalStatus(false));
      navigate('/organisation');
    }
  }, [organizationApprovalSuccess]);

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
          disabled
        />
        <InputTextField
          id="url"
          name="url"
          label="Website URL"
          value={organisationFormData?.url}
          onChange={() => {}}
          fieldType="text"
          disabled
        />
        <TextArea
          id="description"
          name="description"
          label="Description"
          rows={3}
          value={organisationFormData?.description}
          onChange={() => {}}
          disabled
        />
        <InputTextField
          id="odk_central_url"
          name="odk_central_url"
          label="ODK Central URL "
          value={organisationFormData?.odk_central_url}
          onChange={() => {}}
          fieldType="text"
          disabled
        />
        <InputTextField
          id="url"
          name="url"
          label="Community or Organization are you applied for? "
          value={organisationFormData?.community_type}
          onChange={() => {}}
          fieldType="text"
          disabled
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
        <Button
          btnText="Reject"
          btnType="other"
          className="fmtm-font-bold"
          onClick={rejectOrganization}
          isLoading={organizationRejecting}
          loadingText="Rejecting..."
          disabled={organizationApproving}
        />
        <Button
          btnText="Verify"
          btnType="primary"
          className="fmtm-font-bold"
          onClick={approveOrganization}
          isLoading={organizationApproving}
          loadingText="Verifying..."
          disabled={organizationRejecting}
        />
      </div>
    </div>
  );
};

export default OrganizationForm;
