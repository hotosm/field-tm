import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import UserTab from '@/components/ManageProject/User';
import AssetModules from '@/shared/AssetModules.js';
import { GetIndividualProjectDetails } from '@/api/CreateProjectService';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import Button from '@/components/common/Button';
import InputTextField from '@/components/common/InputTextField';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/RadixComponents/Dialog';
import { DeleteProjectService } from '@/api/CreateProjectService';
import EditDetails from '@/components/ManageProject/Details';
import FormUpdate from '@/components/ManageProject/Form';
import { useIsOrganizationAdmin, useIsProjectManager } from '@/hooks/usePermissions';
import Forbidden from '@/views/Forbidden';
import ManageProjectSkeleton from '@/components/Skeletons/ManageProject';
import { project_status } from '@/types/enums';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const ManageProject = () => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const navigate = useNavigate();
  const projectId = params.id;

  const editProjectDetails = useAppSelector((state) => state.createproject.editProjectDetails);
  const isProjectDeletePending = useAppSelector((state) => state.createproject.isProjectDeletePending);
  const projectDetailsLoading = useAppSelector((state) => state.createproject.projectDetailsLoading);

  const tabList = [
    { id: 'details', name: 'Details', icon: <AssetModules.InfoIcon className="!fmtm-text-[1.125rem]" />, show: true },
    {
      id: 'form',
      name: 'Form',
      icon: <AssetModules.SubmissionIcon className="!fmtm-text-[1.125rem]" />,
      show: editProjectDetails.status === project_status.PUBLISHED,
    },
    {
      id: 'users',
      name: 'Users',
      icon: <AssetModules.PersonIcon className="!fmtm-text-[1.125rem]" />,
      show: editProjectDetails.status === project_status.PUBLISHED,
    },
  ];

  const isProjectManager = useIsProjectManager(projectId as string);
  const isOrganizationAdmin = useIsOrganizationAdmin(editProjectDetails.organisation_id as null | number);

  const [selectedTab, setSelectedTab] = useState('details');
  const [toggleDeleteModal, setToggleDeleteModal] = useState(false);
  const [confirmProjectName, setConfirmProjectName] = useState('');

  const getContent = (tab: string) => {
    switch (tab) {
      case 'users':
        return <UserTab />;
      case 'details':
        return <EditDetails projectId={projectId} />;
      case 'form':
        return <FormUpdate projectId={projectId} />;
      default:
        return <></>;
    }
  };

  useEffect(() => {
    dispatch(GetIndividualProjectDetails(`${VITE_API_URL}/projects/${projectId}?project_id=${projectId}`));
  }, [projectId]);

  if (!projectDetailsLoading && !isProjectManager && !isOrganizationAdmin) return <Forbidden />;

  return (
    <div className="fmtm-h-full fmtm-flex fmtm-flex-col fmtm-py-3 fmtm-gap-5">
      <div className="fmtm-flex fmtm-items-center">
        <AssetModules.ChevronLeftIcon
          className="!fmtm-w-[1.125rem] fmtm-mx-1 hover:fmtm-text-black hover:fmtm-scale-125 !fmtm-duration-200 fmtm-cursor-pointer fmtm-text-grey-800"
          onClick={() => navigate(`/project/${projectId}`)}
        />
        <h4 className="fmtm-text-grey-800">Manage Project</h4>
      </div>
      {projectDetailsLoading ? (
        <ManageProjectSkeleton />
      ) : (
        <div className="sm:fmtm-flex-1 fmtm-flex fmtm-flex-col sm:fmtm-flex-row fmtm-gap-5 sm:fmtm-overflow-hidden">
          {/* left container */}
          <div className="fmtm-bg-white fmtm-h-full fmtm-rounded-xl sm:fmtm-w-[17.5rem] fmtm-p-6 fmtm-flex sm:fmtm-flex-col fmtm-flex-wrap sm:fmtm-flex-nowrap fmtm-gap-x-5">
            <div className="fmtm-flex-1 fmtm-flex sm:fmtm-flex-col fmtm-h-fit">
              {tabList.map(
                (tab) =>
                  tab.show && (
                    <button
                      key={tab.id}
                      onClick={() => setSelectedTab(tab.id)}
                      className={`fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-px-5 fmtm-py-3 fmtm-rounded fmtm-duration-200 ${
                        selectedTab === tab.id ? 'fmtm-text-red-medium fmtm-bg-red-light' : 'hover:fmtm-text-red-medium'
                      }`}
                    >
                      {tab.icon} {tab.name}
                    </button>
                  ),
              )}
            </div>
            <Dialog open={toggleDeleteModal} onOpenChange={setToggleDeleteModal}>
              <DialogTrigger>
                <Button
                  variant="link-grey"
                  onClick={() => {
                    setToggleDeleteModal(true);
                  }}
                  className="fmtm-mx-auto"
                >
                  <AssetModules.DeleteIcon className="!fmtm-text-[1.125rem]" /> Delete Project
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Delete Project?</DialogTitle>
                </DialogHeader>
                <div>
                  <p className="fmtm-body-lg fmtm-mb-1">Please type the project name to confirm.</p>
                  <InputTextField
                    fieldType="text"
                    value={confirmProjectName}
                    onChange={(e) => setConfirmProjectName(e.target.value)}
                  />
                  <div className="fmtm-flex fmtm-justify-end fmtm-items-center fmtm-mt-4 fmtm-gap-x-2">
                    <Button variant="link-grey" onClick={() => setToggleDeleteModal(false)}>
                      Cancel
                    </Button>
                    <Button
                      variant="primary-red"
                      isLoading={isProjectDeletePending}
                      disabled={confirmProjectName !== editProjectDetails?.name}
                      onClick={() => dispatch(DeleteProjectService(`${VITE_API_URL}/projects/${projectId}`, navigate))}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          {/* right container */}
          <div
            className={`fmtm-h-full fmtm-rounded-xl fmtm-w-full ${selectedTab !== 'users' ? 'fmtm-max-w-[54rem] sm:fmtm-overflow-y-scroll sm:scrollbar' : 'md:fmtm-w-[calc(100%-17.5rem)]'}`}
          >
            {getContent(selectedTab)}
          </div>
        </div>
      )}
    </div>
  );
};

export default ManageProject;
