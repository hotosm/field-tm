import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Tooltip } from '@mui/material';
import Button from '@/components/common/Button';
import AssetModules from '@/shared/AssetModules';
import { GetIndividualOrganizationService, GetOrganizationAdminsService } from '@/api/OrganisationService';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { useIsOrganizationAdmin } from '@/hooks/usePermissions';
import UserListSkeleton from '@/components/Skeletons/OrganizationDashboard/UserListSkeleton';
import OrganizationInfoSkeleton from '@/components/Skeletons/OrganizationDashboard/OrganizationInfoSkeleton';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const OrganizationAdminList = () => {
  const organizationAdmins = useAppSelector((state) => state.organisation.organizationAdmins);
  const organizationAdminsLoading = useAppSelector((state) => state.organisation.getOrganizationAdminsLoading);

  if (organizationAdminsLoading) return <UserListSkeleton />;

  return (
    <div className="fmtm-flex fmtm-items-center">
      {organizationAdmins.slice(0, 5).map((user, index) => (
        <Tooltip key={user.user_sub} title={user.username} arrow>
          <div
            style={{ zIndex: organizationAdmins.length - index }}
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
      {organizationAdmins.length <= 4 ? null : (
        <Tooltip
          title={
            <ul>
              {organizationAdmins.slice(5).map((user) => (
                <li key={user.user_sub}>{user.username}</li>
              ))}
            </ul>
          }
          arrow
        >
          <p className="fmtm-ml-[0.8rem] fmtm-body-lg-medium fmtm-cursor-pointer">
            +{organizationAdmins.slice(5).length}
          </p>
        </Tooltip>
      )}
    </div>
  );
};

const OrganizationInfo = () => {
  const params = useParams();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const organizationId = params.id;
  const isOrganizationAdmin = useIsOrganizationAdmin(+(organizationId as string));

  const organization = useAppSelector((state) => state.organisation.organisationFormData);
  const organizationLoading = useAppSelector((state) => state.organisation.organisationFormDataLoading);

  useEffect(() => {
    if (!organizationId) return;
    dispatch(GetIndividualOrganizationService(`${VITE_API_URL}/organisation/${organizationId}`));
  }, [organizationId]);

  useEffect(() => {
    if (!organizationId) return;
    dispatch(GetOrganizationAdminsService(`${VITE_API_URL}/organisation/org-admins`, { org_id: +organizationId }));
  }, [organizationId]);

  if (organizationLoading) return <OrganizationInfoSkeleton />;

  return (
    <div className="fmtm-flex fmtm-justify-between fmtm-flex-wrap sm:fmtm-flex-nowrap fmtm-gap-x-8 fmtm-gap-y-2 fmtm-bg-white fmtm-rounded-lg fmtm-p-4">
      <div className="fmtm-flex fmtm-gap-x-6">
        <div className="fmtm-w-[4.688rem] fmtm-min-w-[4.688rem] fmtm-min-h-[4.688rem] fmtm-max-w-[4.688rem] fmtm-max-h-[4.688rem]">
          {organization?.logo ? (
            <img src={organization?.logo} className="fmtm-w-full" alt="organization-logo" />
          ) : (
            <div className="fmtm-bg-[#757575] fmtm-w-full fmtm-h-full fmtm-rounded-full fmtm-flex fmtm-items-center fmtm-justify-center">
              <h2 className="fmtm-text-white">{organization?.name?.[0]}</h2>
            </div>
          )}
        </div>
        <div>
          <h3 className="fmtm-mb-2">{organization?.name}</h3>
          <p className="fmtm-body-lg xl:fmtm-w-[39rem] xl:fmtm-max-w-[39rem] fmtm-line-clamp-3 fmtm-overflow-y-scroll scrollbar">
            {organization?.description}
          </p>
        </div>
      </div>

      <div className="fmtm-text-grey-800">
        <p className="fmtm-body-lg-medium fmtm-mb-1">Organization Admins</p>
        <OrganizationAdminList />
        <a href={organization?.url} target="_" className="fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-mt-3 fmtm-mb-1">
          <AssetModules.LinkIcon className="!fmtm-text-lg" />
          <p className="fmtm-body-lg-medium">{organization?.url}</p>
        </a>
        <a href={`mailto:${organization?.associated_email}`} className="fmtm-flex fmtm-items-center fmtm-gap-2">
          <AssetModules.AlternateEmailIcon className="!fmtm-text-lg" />
          <p className="fmtm-body-lg-medium">{organization?.associated_email}</p>
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
