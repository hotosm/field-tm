import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import InputTextField from '@/components/common/InputTextField';
import TextArea from '@/components/common/TextArea';
import Button from '@/components/common/Button';
import { useAppDispatch } from '@/types/reduxTypes';
import RadioButton from '@/components/common/RadioButton';
import type { radioOptionsType } from '@/models/organisation/organisationModel';
import FormFieldSkeletonLoader from '@/components/Skeletons/common/FormFieldSkeleton';
import {
  useApproveOrganisationMutation,
  useDeleteUnapprovedOrganisationMutation,
  useGetOrganisationDetailQuery,
} from '@/api/organisation';
import { CommonActions } from '@/store/slices/CommonSlice';

const odkTypeOptions: radioOptionsType[] = [
  { name: 'odk_server_type', value: 'OWN', label: 'Own ODK server' },
  { name: 'odk_server_type', value: 'HOT', label: "HOT's ODK server" },
];

const OrganizationForm = () => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const navigate = useNavigate();
  const organizationId = params.id;

  const { data: organisationData, isLoading: organisationDataLoading } = useGetOrganisationDetailQuery({
    org_id: +organizationId!,
    params: { org_id: +organizationId! },
    options: {
      queryKey: ['organization', +organizationId!],
      enabled: !!organizationId,
    },
  });

  const { mutate: approveOrganization, isPending: isOrganizationApproving } = useApproveOrganisationMutation({
    params: { org_id: +organizationId!, set_primary_org_odk_server: !organisationData?.odk_central_url },
    options: {
      onSuccess: () => {
        dispatch(CommonActions.SetSnackBar({ message: 'Organization approved successfully', variant: 'success' }));
        navigate('/organization');
      },
      onError: ({ response }) => {
        dispatch(CommonActions.SetSnackBar({ message: response?.data?.message || 'Failed to approve organization' }));
      },
    },
  });

  const { mutate: rejectOrganization, isPending: isOrganizationRejecting } = useDeleteUnapprovedOrganisationMutation({
    id: +organizationId!,
    options: {
      onSuccess: () => {
        dispatch(CommonActions.SetSnackBar({ message: 'Organization rejected successfully', variant: 'success' }));
        navigate('/organization');
      },
      onError: ({ response }) => {
        dispatch(CommonActions.SetSnackBar({ message: response?.data?.message || 'Failed to reject organization' }));
      },
    },
  });

  if (organisationDataLoading)
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
          value={organisationData?.name || ''}
          onChange={() => {}}
          fieldType="text"
          disabled
        />
        <InputTextField
          id="url"
          name="url"
          label="Website URL"
          value={organisationData?.url || ''}
          onChange={() => {}}
          fieldType="text"
          disabled
        />
        <InputTextField
          id="associated_email"
          name="associated_email"
          label="Email"
          value={organisationData?.associated_email || ''}
          onChange={() => {}}
          fieldType="text"
          disabled
        />
        <TextArea
          id="description"
          name="description"
          label="Description"
          rows={3}
          value={organisationData?.description || ''}
          onChange={() => {}}
          disabled
        />
        <RadioButton
          topic="ODK Server Type"
          options={odkTypeOptions}
          direction="column"
          value={organisationData?.odk_central_url ? 'OWN' : 'HOT'}
          onChangeData={() => {}}
          className="fmtm-text-base fmtm-text-[#7A7676] fmtm-mt-1"
        />
        {organisationData?.odk_central_url && (
          <InputTextField
            id="odk_central_url"
            name="odk_central_url"
            label="ODK Central URL "
            value={organisationData?.odk_central_url}
            onChange={() => {}}
            fieldType="text"
            disabled
          />
        )}
        <InputTextField
          id="url"
          name="url"
          label="Community or Organization are you applied for? "
          value={organisationData?.community_type || ''}
          onChange={() => {}}
          fieldType="text"
          disabled
        />
        <div>
          <p className="fmtm-text-[1rem] fmtm-font-semibold fmtm-mb-2">Logo</p>
          {organisationData?.logo ? (
            <div>
              <img src={organisationData?.logo} alt="" className="fmtm-h-[100px] fmtm-rounded-sm fmtm-border-[1px]" />
            </div>
          ) : (
            <p className="fmtm-ml-3">-</p>
          )}
        </div>
      </div>
      <div className="fmtm-flex fmtm-items-center fmtm-justify-center fmtm-gap-6 fmtm-mt-8 lg:fmtm-mt-16">
        <Button
          variant="secondary-red"
          onClick={() => rejectOrganization()}
          isLoading={isOrganizationRejecting}
          disabled={isOrganizationApproving}
        >
          Reject
        </Button>
        <Button
          variant="primary-red"
          onClick={() => approveOrganization()}
          isLoading={isOrganizationApproving}
          disabled={isOrganizationRejecting}
        >
          Verify
        </Button>
      </div>
    </div>
  );
};

export default OrganizationForm;
