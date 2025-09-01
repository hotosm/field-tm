import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Tooltip } from '@mui/material';
import Button from '@/components/common/Button';
import AssetModules from '@/shared/AssetModules';
import { useIsOrganizationAdmin } from '@/hooks/usePermissions';
import UserListSkeleton from '@/components/Skeletons/OrganizationDashboard/UserListSkeleton';
import OrganizationInfoSkeleton from '@/components/Skeletons/OrganizationDashboard/OrganizationInfoSkeleton';
import { useGetOrganisationAdminsQuery, useGetOrganisationDetailQuery } from '@/api/organisation';

const OrganizationAdminList = ({orgId}: {orgId: number}) => {
   const { data: organisationAdmins, isLoading: isOrganisationAdminsLoading } = useGetOrganisationAdminsQuery({
      params: {org_id: orgId},
      options: { queryKey: ['get-organisation', orgId] },
    });

  if (isOrganisationAdminsLoading) return <UserListSkeleton />;

  return (
    <div className="fmtm-flex fmtm-items-center">
      {organisationAdmins?.slice(0, 5).map((user, index) => (
        <Tooltip key={user.user_sub} title={user.username} arrow>
          <div
            style={{ zIndex: organisationAdmins.length - index }}
            className="fmtm-border fmtm-rounded-full fmtm-h-[1.688rem] fmtm-w-[1.688rem] fmtm-relative fmtm-mr-[-0.5rem] fmtm-bg-white fmtm-overflow-hidden fmtm-cursor-pointer"
          >
            {user.profile_img ? (
              <img
                src={user.profile_img}
                alt="img"
                className="fmtm-rounded-lg"
                style={{ objectFit: 'cover', width: '100%', height: '100%', borderRadius: '50%' }}
              />
            ) : (
              <div className="fmtm-bg-[#757575] fmtm-flex fmtm-justify-center fmtm-items-center fmtm-w-full fmtm-h-full">
                <p className="fmtm-text-white fmtm-font-semibold">
                  {user.username
                    .split(' ')
                    .map((part) => part.charAt(0).toUpperCase())
                    .join('')}
                </p>
              </div>
            )}
          </div>
        </Tooltip>
      ))}
      {organisationAdmins && organisationAdmins?.length <= 4 ? null : (
        <Tooltip
          title={
            <ul>
              {organisationAdmins?.slice(5).map((user) => (
                <li key={user.user_sub}>{user.username}</li>
              ))}
            </ul>
          }
          arrow
        >
          <p className="fmtm-ml-[0.8rem] fmtm-body-lg-medium fmtm-cursor-pointer">
            +{organisationAdmins?.slice(5).length}
          </p>
        </Tooltip>
      )}
    </div>
  );
};

const OrganizationInfo = () => {
  const params = useParams();
  const navigate = useNavigate();

  const organizationId = params.id;
  const isOrganizationAdmin = useIsOrganizationAdmin(+(organizationId as string));

  const { data: organisation, isLoading: isOrganisationLoading } = useGetOrganisationDetailQuery({
    org_id: +organizationId!,
    params: {},
    options: { queryKey: ['get-organisation', organizationId] },
  });

  if (isOrganisationLoading) return <OrganizationInfoSkeleton />;

  return (
    <div className="fmtm-flex fmtm-justify-between fmtm-flex-wrap sm:fmtm-flex-nowrap fmtm-gap-x-8 fmtm-gap-y-2 fmtm-bg-white fmtm-rounded-lg fmtm-p-4">
      <div className="fmtm-flex fmtm-gap-x-6">
        <div className="fmtm-w-[4.688rem] fmtm-min-w-[4.688rem] fmtm-min-h-[4.688rem] fmtm-max-w-[4.688rem] fmtm-max-h-[4.688rem]">
          {organisation?.logo ? (
            <img src={organisation?.logo} className="fmtm-w-full" alt="organization-logo" />
          ) : (
            <div className="fmtm-bg-[#757575] fmtm-w-full fmtm-h-full fmtm-rounded-full fmtm-flex fmtm-items-center fmtm-justify-center">
              <h2 className="fmtm-text-white">{organisation?.name?.[0]}</h2>
            </div>
          )}
        </div>
        <div>
          <h3 className="fmtm-mb-2">{organisation?.name}</h3>
          <p className="fmtm-body-lg xl:fmtm-w-[39rem] xl:fmtm-max-w-[39rem] fmtm-line-clamp-3 fmtm-overflow-y-scroll scrollbar">
            {organisation?.description}
          </p>
        </div>
      </div>

      <div className="fmtm-text-grey-800">
        <p className="fmtm-body-lg-medium fmtm-mb-1">Organization Admins</p>
        <OrganizationAdminList orgId={+organizationId!}/>
        <a href={organisation?.url} target="_" className="fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-mt-3 fmtm-mb-1">
          <AssetModules.LinkIcon className="!fmtm-text-lg" />
          <p className="fmtm-body-lg-medium">{organisation?.url}</p>
        </a>
        <a href={`mailto:${organisation?.associated_email}`} className="fmtm-flex fmtm-items-center fmtm-gap-2">
          <AssetModules.AlternateEmailIcon className="!fmtm-text-lg" />
          <p className="fmtm-body-lg-medium">{organisation?.associated_email}</p>
        </a>
      </div>

      {isOrganizationAdmin && (
        <div className="fmtm-my-auto">
          <Button
            variant="secondary-grey"
            onClick={() => {
              navigate(`/manage/organization/${organizationId}`);
            }}
          >
            <AssetModules.EditIcon className="!fmtm-text-lg" />
            Manage Organization
          </Button>
        </div>
      )}
    </div>
  );
};

export default OrganizationInfo;
