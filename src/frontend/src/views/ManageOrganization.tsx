import React, { useEffect, useState } from 'react';
import AssetModules from '@/shared/AssetModules';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { DeleteOrganizationService, GetIndividualOrganizationService } from '@/api/OrganisationService';
import Button from '@/components/common/Button';
import CreateEditOrganizationForm from '@/components/CreateEditOrganization/CreateEditOrganizationForm';
import { useIsOrganizationAdmin } from '@/hooks/usePermissions';
import NoAccessComponent from './NoAccessComponent';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/RadixComponents/Dialog';
import InputTextField from '@/components/common/InputTextField';
import ManageAdmins from '@/components/ManageOrganization/ManageAdmins';

const API_URL = import.meta.env.VITE_API_URL;

const tabList = [
  { name: 'Details', id: 'details', icon: <AssetModules.InfoIcon className="!fmtm-text-[1.125rem]" /> },
  { name: 'Admins', id: 'admins', icon: <AssetModules.PeopleAltIcon className="!fmtm-text-[1.125rem]" /> },
];

const ManageOrganization = () => {
  const navigate = useNavigate();
  const params = useParams();
  const dispatch = useAppDispatch();

  const organizationId = params.id;

  const isOrganizationAdmin = useIsOrganizationAdmin(+(organizationId as string));
  if (organizationId && !isOrganizationAdmin) return <NoAccessComponent />;

  const organization = useAppSelector((state) => state.organisation.organisationFormData);
  const organizationDeleteLoading = useAppSelector((state) => state.organisation.organizationDeleteLoading);
  const [selectedTab, setSelectedTab] = useState('details');
  const [toggleDeleteOrgModal, setToggleDeleteOrgModal] = useState(false);
  const [confirmOrgName, setConfirmOrgName] = useState('');

  useEffect(() => {
    if (organizationId) {
      dispatch(GetIndividualOrganizationService(`${API_URL}/organisation/${organizationId}`));
    }
  }, [organizationId]);

  const getContent = (tab: string) => {
    switch (tab) {
      case 'details':
        return <CreateEditOrganizationForm organizationId={organizationId || ''} />;
      case 'admins':
        return <ManageAdmins />;
      default:
        return <></>;
    }
  };

  return (
    <>
      <div className="fmtm-h-full fmtm-flex fmtm-flex-col fmtm-py-3 fmtm-gap-5">
        <div className="fmtm-flex fmtm-items-center">
          <AssetModules.ChevronLeftIcon
            className="!fmtm-w-[1.125rem] fmtm-mx-1 hover:fmtm-text-black hover:fmtm-scale-125 !fmtm-duration-200 fmtm-cursor-pointer fmtm-text-grey-800"
            onClick={() => navigate('/')}
          />
          <h4 className="fmtm-text-grey-800">Manage Organization</h4>
        </div>
        <div className="sm:fmtm-flex-1 fmtm-flex fmtm-justify-center fmtm-flex-col sm:fmtm-flex-row fmtm-gap-5 sm:fmtm-overflow-hidden">
          {/* left container */}
          <div className="fmtm-bg-white fmtm-h-full fmtm-rounded-xl sm:fmtm-w-[17.5rem] fmtm-p-6 fmtm-flex sm:fmtm-flex-col fmtm-flex-wrap sm:fmtm-flex-nowrap fmtm-gap-x-5">
            <div className="fmtm-flex fmtm-flex-col fmtm-items-center fmtm-mx-auto fmtm-gap-3 fmtm-mb-2 sm:fmtm-mb-6">
              <div className="fmtm-w-[4.688rem] fmtm-min-w-[4.688rem] fmtm-min-h-[4.688rem] fmtm-max-w-[4.688rem] fmtm-max-h-[4.688rem]">
                {organization?.logo ? (
                  <img src={organization?.logo} className="fmtm-w-full" alt="organization-logo" />
                ) : (
                  <div className="fmtm-bg-[#757575] fmtm-w-full fmtm-h-full fmtm-rounded-full fmtm-flex fmtm-items-center fmtm-justify-center">
                    <h2 className="fmtm-text-white">{organization?.name?.[0]}</h2>
                  </div>
                )}
              </div>
              <p className="fmtm-body-md-semibold">{organization?.name}</p>
            </div>
            <div className="fmtm-flex-1 fmtm-flex sm:fmtm-flex-col fmtm-h-fit">
              {tabList.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setSelectedTab(tab.id)}
                  className={`fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-px-5 fmtm-py-3 fmtm-rounded fmtm-duration-200 ${
                    selectedTab === tab.id ? 'fmtm-text-red-medium fmtm-bg-red-light' : 'hover:fmtm-text-red-medium'
                  }`}
                >
                  {tab.icon} {tab.name}
                </button>
              ))}
            </div>
            <Dialog open={toggleDeleteOrgModal} onOpenChange={setToggleDeleteOrgModal}>
              <DialogTrigger>
                <Button
                  variant="link-grey"
                  onClick={() => {
                    setToggleDeleteOrgModal(true);
                  }}
                  className="fmtm-mx-auto"
                >
                  <AssetModules.DeleteIcon className="!fmtm-text-[1.125rem]" /> Delete Organization
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Delete Organization?</DialogTitle>
                </DialogHeader>
                <div>
                  <p className="fmtm-body-lg fmtm-mb-1">Please type the organization name to confirm.</p>
                  <InputTextField
                    fieldType="text"
                    value={confirmOrgName}
                    onChange={(e) => setConfirmOrgName(e.target.value)}
                  />
                  <div className="fmtm-flex fmtm-justify-end fmtm-items-center fmtm-mt-4 fmtm-gap-x-2">
                    <Button variant="link-grey" onClick={() => setToggleDeleteOrgModal(false)}>
                      Cancel
                    </Button>
                    <Button
                      variant="primary-red"
                      isLoading={organizationDeleteLoading}
                      disabled={confirmOrgName !== organization?.name}
                      onClick={() =>
                        dispatch(DeleteOrganizationService(`${API_URL}/organisation/${organizationId}`, navigate))
                      }
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          {/* right container */}
          <div className="fmtm-bg-white fmtm-h-full fmtm-rounded-xl fmtm-w-full fmtm-max-w-[54rem] sm:fmtm-overflow-y-scroll sm:scrollbar">
            {getContent(selectedTab)}
          </div>
        </div>
      </div>
    </>
  );
};

export default ManageOrganization;
