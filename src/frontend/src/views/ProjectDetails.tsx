import React, { useEffect, useState } from 'react';
import '../../node_modules/ol/ol.css';
import '../styles/home.scss';
import TaskActivity from '@/components/ProjectDetails/Tabs/TaskActivity';
import { ProjectById, GetEntityStatusList, GetOdkEntitiesGeojson } from '@/api/Project';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import AssetModules from '@/shared/AssetModules';
import GenerateBasemap from '@/components/GenerateBasemap';
import TaskSelectionPopup from '@/components/ProjectDetails/TaskSelectionPopup';
import FeatureSelectionPopup from '@/components/ProjectDetails/FeatureSelectionPopup';
import DialogTaskActions from '@/components/DialogTaskActions';
import MobileFooter from '@/components/ProjectDetails/MobileFooter';
import MobileActivitiesContents from '@/components/ProjectDetails/MobileActivitiesContents';
import BottomSheet from '@/components/common/BottomSheet';
import MobileProjectInfoContent from '@/components/ProjectDetails/MobileProjectInfoContent';
import { Link, useNavigate, useParams } from 'react-router-dom';
import ProjectOptions from '@/components/ProjectDetails/ProjectOptions';
import Button from '@/components/common/Button';
import ProjectInfo from '@/components/ProjectDetails/Tabs/ProjectInfo';
import useOutsideClick from '@/hooks/useOutsideClick';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import Comments from '@/components/ProjectDetails/Tabs/Comments';
import Instructions from '@/components/ProjectDetails/Tabs/Instructions';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import ProjectDetailsMap from '@/components/ProjectDetails/ProjectDetailsMap';
import FolderManagedIcon from '@/assets/icons/folderManagedIcon.svg';
import boltIcon from '@/assets/icons/boltIcon.svg';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/RadixComponents/Resizable';
import TaskList from '@/components/ProjectDetails/Tabs/TaskList';
import { Tooltip } from '@mui/material';
import { Skeleton } from '@/components/Skeletons';
import { useIsOrganizationAdmin, useIsProjectManager } from '@/hooks/usePermissions';
import { field_mapping_app, project_status } from '@/types/enums';

const VITE_API_URL = import.meta.env.VITE_API_URL;

type tabType = 'project_info' | 'task_activity' | 'comments' | 'instructions' | 'task_list';

const ProjectDetails = () => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const navigate = useNavigate();
  const [divRef, toggle, handleToggle] = useOutsideClick();

  const projectId: string | undefined = params.id;

  const [map, setMap] = useState();
  const [selectedTaskArea, setSelectedTaskArea] = useState<Record<string, any> | null>(null);
  const [selectedTaskFeature, setSelectedTaskFeature] = useState();
  const [selectedTab, setSelectedTab] = useState<tabType>('project_info');

  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);
  const projectTaskBoundries = useAppSelector((state) => state.project.projectTaskBoundries);
  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const selectedTask = useAppSelector((state) => state.task.selectedTask);
  const selectedFeatureProps = useAppSelector((state) => state.task.selectedFeatureProps);
  const mobileFooterSelection = useAppSelector((state) => state.project.mobileFooterSelection);
  const projectDetailsLoading = useAppSelector((state) => state.project.projectDetailsLoading);
  const taskModalStatus = useAppSelector((state) => state.project.taskModalStatus);

  const isProjectManager = useIsProjectManager(projectId as string);
  const isOrganizationAdmin = useIsOrganizationAdmin(projectInfo.organisation_id as number);

  const tabList: { id: tabType; name: string; show: boolean }[] = [
    { id: 'project_info', name: 'Project Info', show: true },
    { id: 'task_activity', name: 'Task Activity', show: projectInfo.field_mapping_app !== field_mapping_app.QField },
    { id: 'comments', name: 'Comments', show: projectInfo.field_mapping_app !== field_mapping_app.QField },
    { id: 'instructions', name: 'Instructions', show: true },
    { id: 'task_list', name: 'Task List', show: projectInfo.field_mapping_app !== field_mapping_app.QField },
  ];

  useDocumentTitle(projectInfo.name && !projectDetailsLoading ? projectInfo.name : 'Project Details');

  //Fetch project for the first time
  useEffect(() => {
    if (!projectId) return;

    dispatch(ProjectActions.SetNewProjectTrigger());
    if (projectTaskBoundries.findIndex((project) => project.id.toString() === projectId) == -1) {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(projectId));
    } else {
      dispatch(ProjectActions.SetProjectTaskBoundries([]));
      dispatch(ProjectById(projectId));
    }
    return () => {};
  }, [projectId]);

  useEffect(() => {
    if (mobileFooterSelection !== '') {
      dispatch(ProjectActions.ToggleGenerateMbTilesModalStatus(false));
    }
  }, [mobileFooterSelection]);

  useEffect(() => {
    if (taskModalStatus) {
      dispatch(ProjectActions.ToggleTaskModalStatus(false));
    }
  }, []);

  useEffect(() => {
    if (taskModalStatus) {
      setSelectedTab('task_activity');
    } else {
      setSelectedTab('project_info');
    }
  }, [taskModalStatus]);

  const getEntityStatusList = () => {
    dispatch(GetEntityStatusList(`${VITE_API_URL}/projects/${projectId}/entities/statuses`));
  };

  const getOdkEntitiesGeojson = () => {
    dispatch(GetOdkEntitiesGeojson(`${VITE_API_URL}/projects/${projectId}/entities`));
  };

  // temporary fix: only call api if field_mapping_app is not QField
  useEffect(() => {
    if (projectId && projectInfo?.id === +projectId && projectInfo?.field_mapping_app !== field_mapping_app.QField) {
      getEntityStatusList();
      getOdkEntitiesGeojson();
    }

    return () => {
      dispatch(ProjectActions.ClearProjectFeatures());
    };
  }, [projectInfo]);

  const getTabContent = (tabState: tabType) => {
    switch (tabState) {
      case 'project_info':
        return <ProjectInfo />;
      case 'task_activity':
        return <TaskActivity params={params} state={projectTaskBoundries} defaultTheme={defaultTheme} map={map} />;
      case 'comments':
        return <Comments projectStatus={projectInfo?.status as project_status} />;
      case 'instructions':
        return <Instructions instructions={projectInfo?.instructions} />;
      case 'task_list':
        return <TaskList map={map} setSelectedTab={setSelectedTab} />;
      default:
        return <></>;
    }
  };

  const getMobileBottomSheetContent = (
    mobileTabState: '' | 'projectInfo' | 'activities' | 'comment' | 'instructions',
  ) => {
    switch (mobileTabState) {
      case 'projectInfo':
        return <MobileProjectInfoContent projectInfo={projectInfo} />;
      case 'activities':
        return <MobileActivitiesContents map={map} />;
      case 'instructions':
        return (
          <div className="fmtm-mb-[10vh]">
            <Instructions instructions={projectInfo?.instructions} />
          </div>
        );
      case 'comment':
        return (
          <div className="fmtm-mb-[10vh]">
            <Comments />
          </div>
        );
      default:
        return <></>;
    }
  };

  return (
    <div className="fmtm-bg-grey-100 !fmtm-h-[100dvh] md:!fmtm-h-full md:fmtm-overflow-hidden">
      {/* Customized Modal For Generate Tiles */}
      <GenerateBasemap projectInfo={projectInfo} />

      <div className="fmtm-h-full fmtm-w-full">
        {/* upper div */}
        <div className="fmtm-w-full fmtm-hidden md:fmtm-flex fmtm-items-center fmtm-justify-between fmtm-gap-2">
          <div className="fmtm-flex fmtm-items-center">
            <AssetModules.ChevronLeftIcon
              className="!fmtm-w-[1.125rem] fmtm-mx-1 hover:fmtm-text-black hover:fmtm-scale-125 !fmtm-duration-200 fmtm-cursor-pointer"
              onClick={() => navigate('/explore')}
            />
            <h5 className="fmtm-line-clamp-1" title={projectInfo.name}>
              {projectInfo.name}
            </h5>
            {projectInfo.visibility === 'PRIVATE' && (
              <Tooltip title="Private Project" arrow>
                <AssetModules.LockOutlinedIcon className="fmtm-text-red-medium !fmtm-text-[19px] fmtm-mx-1 fmtm-cursor-pointer" />
              </Tooltip>
            )}
          </div>
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
            <Button
              variant="secondary-grey"
              onClick={() => dispatch(ProjectActions.ToggleGenerateMbTilesModalStatus(true))}
            >
              <img src={boltIcon} alt="bolt icon" />
              Generate Basemap
            </Button>
            <div className="fmtm-relative fmtm-w-1/2" ref={divRef}>
              <Button variant="secondary-grey" className="fmtm-w-full" onClick={handleToggle}>
                <AssetModules.FileDownloadOutlinedIcon className="!fmtm-text-[1.125rem]" />
                Download
              </Button>
              <div
                className={`fmtm-flex fmtm-gap-4 fmtm-absolute fmtm-duration-200 fmtm-z-[1000] fmtm-bg-grey-100 fmtm-px-2 fmtm-py-[2px] fmtm-rounded ${
                  toggle ? 'fmtm-right-0 fmtm-top-[3rem]' : '-fmtm-right-[15rem] fmtm-top-[3rem]'
                }`}
              >
                <ProjectOptions />
              </div>
            </div>
          </div>
        </div>
        <div className="fmtm-flex fmtm-h-[calc(100%-3rem)] fmtm-gap-6 fmtm-mt-0 md:fmtm-mt-2">
          <ResizablePanelGroup direction="horizontal" className="fmtm-gap-3">
            <ResizablePanel defaultSize={30} className="fmtm-hidden md:fmtm-flex md:fmtm-min-w-[22rem]">
              <div className="fmtm-w-full fmtm-h-full fmtm-hidden md:fmtm-flex fmtm-flex-col">
                <div
                  className="fmtm-flex fmtm-flex-col fmtm-gap-5 fmtm-flex-1"
                  style={{ height: `${selectedTab === 'comments' ? 'calc(100% - 500px)' : 'calc(100% - 103px)'}` }}
                >
                  <div className="fmtm-overflow-y-hidden fmtm-overflow-x-scroll scrollbar fmtm-min-h-fit">
                    <div className="fmtm-flex fmtm-border-b fmtm-border-grey-200 fmtm-gap-3">
                      {tabList.map((tab) => {
                        if (!tab.show) return null;
                        return (
                          <button
                            key={tab.id}
                            className={`fmtm-body-md fmtm-rounded-none fmtm-border-b fmtm-py-1 fmtm-px-5 fmtm-duration-200 fmtm-w-fit fmtm-text-grey-900 fmtm-text-nowrap ${
                              selectedTab === tab.id ? 'fmtm-border-primaryRed fmtm-button' : 'fmtm-border-transparent'
                            } ${(taskModalStatus && (tab.id === 'project_info' || tab.id === 'instructions' || tab.id === 'task_list')) || (!taskModalStatus && (tab.id === 'task_activity' || tab.id === 'comments')) ? 'fmtm-hidden' : ''}`}
                            onClick={() => setSelectedTab(tab.id)}
                          >
                            {tab.name}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                  {getTabContent(selectedTab)}
                </div>
                {selectedTab !== 'comments' && (
                  <div className="fmtm-flex fmtm-gap-[0.625rem]">
                    {projectDetailsLoading ? (
                      <>
                        <Skeleton className="fmtm-w-1/2 fmtm-h-[2.4rem]" />
                        <Skeleton className="fmtm-w-1/2 fmtm-h-[2.4rem]" />
                      </>
                    ) : (
                      <>
                        {(isProjectManager || isOrganizationAdmin) && (
                          <Link
                            to={`/manage/project/${params?.id}`}
                            className={`${projectInfo.field_mapping_app !== field_mapping_app.QField ? 'fmtm-w-1/2' : 'fmtm-w-full'}`}
                          >
                            <Button variant="secondary-grey" className="fmtm-w-full">
                              <img src={FolderManagedIcon} alt="Manage Project" className="fmtm-h-5 fmtm-w-5" />
                              Manage Project
                            </Button>
                          </Link>
                        )}
                        {projectInfo.field_mapping_app !== field_mapping_app.QField && (
                          <Link
                            to={`/project-submissions/${projectId}`}
                            className={`${isProjectManager || isOrganizationAdmin ? 'fmtm-w-1/2' : 'fmtm-w-full'}`}
                          >
                            <Button variant="secondary-grey" className="fmtm-w-full">
                              <AssetModules.BarChartOutlinedIcon className="fmtm-text-[1.125rem]" />
                              View Statistics
                            </Button>
                          </Link>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle className="fmtm-bg-grey-200 fmtm-hidden md:fmtm-flex" />
            <ResizablePanel defaultSize={70} className="md:fmtm-min-w-[22rem] fmtm-relative">
              {projectId && (
                <div className="fmtm-relative md:fmtm-static fmtm-flex-grow fmtm-h-full md:fmtm-rounded-xl fmtm-overflow-hidden">
                  <ProjectDetailsMap
                    setSelectedTaskArea={setSelectedTaskArea}
                    setSelectedTaskFeature={setSelectedTaskFeature}
                    setMap={setMap}
                  />
                </div>
              )}
              {selectedTaskArea && selectedTask && !selectedTaskFeature && (
                <TaskSelectionPopup
                  taskId={selectedTask}
                  feature={selectedTaskArea}
                  body={
                    <div>
                      <DialogTaskActions feature={selectedTaskArea} taskId={selectedTask} />
                    </div>
                  }
                />
              )}
              {selectedTaskFeature && (
                <FeatureSelectionPopup
                  featureProperties={selectedFeatureProps}
                  taskId={selectedTask}
                  setSelectedTaskFeature={setSelectedTaskFeature}
                />
              )}
            </ResizablePanel>
          </ResizablePanelGroup>
          <div
            className="fmtm-absolute fmtm-top-4 fmtm-left-4 fmtm-bg-white fmtm-rounded-full fmtm-p-1 hover:fmtm-bg-red-50 fmtm-duration-300 fmtm-border-[1px] md:fmtm-hidden fmtm-cursor-pointer"
            onClick={() => navigate('/explore')}
          >
            <AssetModules.ArrowBackIcon className="fmtm-text-grey-800" />
          </div>
          {['projectInfo', 'activities', 'instructions', 'comment'].includes(mobileFooterSelection) && (
            <BottomSheet
              body={getMobileBottomSheetContent(mobileFooterSelection)}
              onClose={() => dispatch(ProjectActions.SetMobileFooterSelection(''))}
            />
          )}
          <MobileFooter />
        </div>
      </div>
    </div>
  );
};

export default ProjectDetails;
