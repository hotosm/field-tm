import React, { useEffect } from 'react';
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
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import RadioButton from '@/components/common/RadioButton';
import { radioOptionsType } from '@/models/organisation/organisationModel';
import FormFieldSkeletonLoader from '@/components/Skeletons/common/FormFieldSkeleton';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const odkTypeOptions: radioOptionsType[] = [
  { name: 'odk_server_type', value: 'OWN', label: 'Own ODK server' },
  { name: 'odk_server_type', value: 'HOT', label: "HOT's ODK server" },
];

const OrganizationForm = () => {
  const dispatch = useAppDispatch();
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
  const organisationFormDataLoading = useAppSelector((state) => state.organisation.organisationFormDataLoading);

  useEffect(() => {
    if (organizationId) {
      dispatch(GetIndividualOrganizationService(`${VITE_API_URL}/organisation/${organizationId}`));
    }
  }, [organizationId]);

  const approveOrganization = () => {
    if (organizationId) {
      dispatch(
        ApproveOrganizationService(`${VITE_API_URL}/organisation/approve`, {
          org_id: +organizationId,
          set_primary_org_odk_server: !organisationFormData?.odk_central_url,
        }),
      );
    }
  };

  const rejectOrganization = () => {
    dispatch(RejectOrganizationService(`${VITE_API_URL}/organisation/unapproved/${organizationId}`));
  };

  // redirect to manage-organization page after approve/reject success
  useEffect(() => {
    if (organizationApprovalSuccess) {
      dispatch(OrganisationAction.SetOrganisationFormData({}));
      dispatch(OrganisationAction.SetOrganizationApprovalStatus(false));
      navigate('/organization');
    }
  }, [organizationApprovalSuccess]);

  if (organisationFormDataLoading)
    return (
      <div className="fmtm-bg-white fmtm-p-5">
        <FormFieldSkeletonLoader count={8} />
      </div>
    );

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
        <InputTextField
          id="associated_email"
          name="associated_email"
          label="Email"
          value={organisationFormData?.associated_email}
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
        <RadioButton
          topic="ODK Server Type"
          options={odkTypeOptions}
          direction="column"
          value={organisationFormData?.odk_central_url ? 'OWN' : 'HOT'}
          onChangeData={() => {}}
          className="fmtm-text-base fmtm-text-[#7A7676] fmtm-mt-1"
        />
        {organisationFormData?.odk_central_url && (
          <InputTextField
            id="odk_central_url"
            name="odk_central_url"
            label="ODK Central URL "
            value={organisationFormData?.odk_central_url}
            onChange={() => {}}
            fieldType="text"
            disabled
          />
        )}
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
          variant="secondary-red"
          onClick={rejectOrganization}
          isLoading={organizationRejecting}
          disabled={organizationApproving}
        >
          Reject
        </Button>
        <Button
          variant="primary-red"
          onClick={approveOrganization}
          isLoading={organizationApproving}
          disabled={organizationRejecting}
        >
          Verify
        </Button>
      </div>
    </div>
  );
};

export default OrganizationForm;
