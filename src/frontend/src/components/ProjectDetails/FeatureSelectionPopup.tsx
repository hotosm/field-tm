// Popup used to display task feature info & link to ODK Collect

import React, { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import AssetModules from '@/shared/AssetModules';
import Button from '@/components/common/Button';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { TaskFeatureSelectionProperties } from '@/store/types/ITask';
import { entity_state, project_status } from '@/types/enums';
import { DeleteEntity } from '@/api/Project';
import { useIsProjectManager } from '@/hooks/usePermissions';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/RadixComponents/Dialog';

const VITE_API_URL = import.meta.env.VITE_API_URL;

type FeatureSelectionPopupPropType = {
  taskId: number | null;
  featureProperties: TaskFeatureSelectionProperties | null;
  setSelectedTaskFeature: (feature: any) => void;
};

const FeatureSelectionPopup = ({
  featureProperties,
  taskId,
  setSelectedTaskFeature,
}: FeatureSelectionPopupPropType) => {
  const dispatch = useAppDispatch();
  const params = useParams();
  const projectId = params.id || '';

  const [toggleDeleteModal, setToggleDeleteModal] = useState(false);

  const taskModalStatus = useAppSelector((state) => state.project.taskModalStatus);
  const entityOsmMap = useAppSelector((state) => state.project.entityOsmMap);
  const entity = entityOsmMap.find(
    (x) => x.osm_id == featureProperties?.osm_id || x.id === featureProperties?.entity_id,
  );
  const submissionIds = entity?.submission_ids ? entity?.submission_ids?.split(',') : [];
  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const isEntityDeleting = useAppSelector((state) => state.project.isEntityDeleting);

  const isProjectManager = useIsProjectManager(projectId);

  const deleteNewEntity = async () => {
    if (!entity?.id) return;
    await dispatch(DeleteEntity(`${VITE_API_URL}/projects/entity/${entity.id}`, +projectId, entity.id));
    setToggleDeleteModal(false);
    setSelectedTaskFeature(undefined);
  };

  return (
    <>
      <Dialog open={toggleDeleteModal} onOpenChange={setToggleDeleteModal}>
        <DialogContent className="!fmtm-z-[10005]">
          <DialogHeader>
            <DialogTitle>Are you sure you want to delete this entity?</DialogTitle>
          </DialogHeader>
          <div className="fmtm-flex fmtm-justify-end fmtm-items-center fmtm-gap-5">
            <Button variant="link-grey" onClick={() => setToggleDeleteModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary-red"
              onClick={() => {
                deleteNewEntity();
              }}
              isLoading={(entity && isEntityDeleting[entity?.id]) || false}
            >
              Delete
            </Button>
          </div>
        </DialogContent>
      </Dialog>
      <div
        className={`fmtm-duration-1000 fmtm-z-50 fmtm-h-fit md:fmtm-max-w-[15rem] ${
          taskModalStatus
            ? 'fmtm-bottom-[1.3rem] md:fmtm-top-[50%] md:-fmtm-translate-y-[35%] fmtm-right-0 fmtm-w-[100vw]'
            : 'fmtm-top-[calc(100vh)] md:fmtm-top-[calc(40vh)] md:fmtm-left-[calc(100vw)]'
        } fmtm-absolute fmtm-rounded-t-3xl fmtm-border-opacity-50`}
      >
        <div
          className={`fmtm-bg-[#fbfbfb] ${
            taskModalStatus
              ? 'sm:fmtm-shadow-[-20px_0px_60px_25px_rgba(0,0,0,0.2)] fmtm-border-b sm:fmtm-border-b-0'
              : ''
          } fmtm-rounded-t-2xl md:fmtm-rounded-tr-none md:fmtm-rounded-l-2xl`}
        >
          <div className="fmtm-flex fmtm-justify-between fmtm-items-center fmtm-gap-2 fmtm-px-3 sm:fmtm-px-5 fmtm-py-2 fmtm-w-full">
            <h4 className="fmtm-text-lg fmtm-font-bold">
              {featureProperties?.osm_id
                ? `Feature: ${featureProperties.osm_id}`
                : `Entity: ${featureProperties?.entity_id}`}
            </h4>
            <div title="Close">
              <AssetModules.CloseIcon
                style={{ width: '20px' }}
                className="hover:fmtm-text-primaryRed fmtm-cursor-pointer"
                onClick={() => {
                  dispatch(ProjectActions.ToggleTaskModalStatus(false));
                  dispatch(ProjectActions.SetSelectedEntityId(null));
                }}
              />
            </div>
          </div>
          {(isProjectManager || isOrganizationAdmin) &&
            entity &&
            entity?.osm_id < 0 &&
            (entity_state[entity.status] === 'READY' || entity_state[entity.status] === 'OPENED_IN_ODK') && (
              <div className="fmtm-gap-2 fmtm-px-3 sm:fmtm-px-5 fmtm-pb-2">
                <Button
                  variant="secondary-red"
                  className="fmtm-w-full"
                  onClick={() => setToggleDeleteModal(true)}
                  isLoading={isEntityDeleting[entity.id] || false}
                >
                  <AssetModules.DeleteOutlinedIcon /> Delete this entity
                </Button>
              </div>
            )}
          {featureProperties?.changeset && (
            <div className="fmtm-h-fit fmtm-px-2 sm:fmtm-px-5 fmtm-py-2 fmtm-border-t">
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-1 fmtm-mt-1">
                <p>
                  <span>Tags: </span>
                  <span className="fmtm-overflow-hidden fmtm-line-clamp-2">{featureProperties?.tags}</span>
                </p>
                <p>
                  <span>Timestamp: </span>
                  <span>{featureProperties?.timestamp}</span>
                </p>
                <p>
                  <span>Changeset: </span>
                  <span>{featureProperties?.changeset}</span>
                </p>
                <p>
                  <span>Version: </span>
                  <span>{featureProperties?.version}</span>
                </p>
              </div>
            </div>
          )}
          {(!submissionIds || submissionIds?.length !== 0) &&
            entity &&
            entity_state[entity.status] !== 'VALIDATED' &&
            projectInfo.status === project_status.PUBLISHED && (
              <div className="fmtm-px-2 sm:fmtm-px-5 fmtm-py-3 fmtm-border-t fmtm-flex fmtm-flex-col fmtm-gap-3">
                {submissionIds?.length > 1 ? (
                  <>
                    {submissionIds?.map((submissionId, index) => (
                      <div
                        key={submissionId}
                        className="fmtm-flex fmtm-flex-col sm:fmtm-flex-row md:fmtm-flex-col sm:fmtm-justify-between sm:fmtm-items-end md:fmtm-items-stretch fmtm-gap-1"
                      >
                        <div>
                          <p className="fmtm-border-b fmtm-w-fit fmtm-border-primaryRed fmtm-leading-5 fmtm-mb-1">
                            Submission #{index + 1}
                          </p>
                          <p className="">ID: {submissionId?.replace('uuid:', '')}</p>
                        </div>
                        <Link to={`/project-submissions/${projectId}/tasks/${taskId}/submission/${submissionId}`}>
                          <Button variant="secondary-red" className="!fmtm-w-full">
                            VALIDATE THIS FEATURE
                          </Button>
                        </Link>
                      </div>
                    ))}
                  </>
                ) : (
                  <Link to={`/project-submissions/${projectId}/tasks/${taskId}/submission/${submissionIds}`}>
                    <Button variant="secondary-red" className="!fmtm-w-full">
                      VALIDATE THIS FEATURE
                    </Button>
                  </Link>
                )}
              </div>
            )}
        </div>
      </div>
    </>
  );
};

export default FeatureSelectionPopup;
