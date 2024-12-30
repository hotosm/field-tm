// Popup used to display task feature info & link to ODK Collect

import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAppSelector } from '@/types/reduxTypes';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import Button from '@/components/common/Button';
import { ProjectActions } from '@/store/slices/ProjectSlice';
import { TaskFeatureSelectionProperties } from '@/store/types/ITask';

type FeatureSelectionPopupPropType = {
  taskId: number;
  featureProperties: TaskFeatureSelectionProperties | null;
};

const FeatureSelectionPopup = ({ featureProperties, taskId }: FeatureSelectionPopupPropType) => {
  const dispatch = CoreModules.useAppDispatch();
  const params = useParams();
  const taskModalStatus = useAppSelector((state) => state.project.taskModalStatus);
  const entityOsmMap = useAppSelector((state) => state.project.entityOsmMap);
  const projectId = params.id || '';
  const entity = entityOsmMap.find((x) => x.osm_id === featureProperties?.osm_id);
  const submissionIds = entity?.submission_ids ? entity?.submission_ids?.split(',') : [];

  return (
    <div
      className={`fmtm-duration-1000 fmtm-z-[10002] fmtm-h-fit ${
        taskModalStatus
          ? 'fmtm-bottom-[4.4rem] md:fmtm-top-[50%] md:-fmtm-translate-y-[35%] fmtm-right-0 fmtm-w-[100vw] md:fmtm-w-[50vw] md:fmtm-max-w-fit'
          : 'fmtm-top-[calc(100vh)] md:fmtm-top-[calc(40vh)] md:fmtm-left-[calc(100vw)] fmtm-w-[100vw] md:fmtm-max-w-[23rem]'
      } fmtm-fixed fmtm-rounded-t-3xl fmtm-border-opacity-50`}
    >
      <div
        className={`fmtm-bg-[#fbfbfb] ${
          taskModalStatus ? 'sm:fmtm-shadow-[-20px_0px_60px_25px_rgba(0,0,0,0.2)] fmtm-border-b sm:fmtm-border-b-0' : ''
        } fmtm-rounded-t-2xl md:fmtm-rounded-tr-none md:fmtm-rounded-l-2xl`}
      >
        <div className="fmtm-flex fmtm-justify-between fmtm-items-center fmtm-gap-2 fmtm-px-3 sm:fmtm-px-5 fmtm-py-2">
          <h4 className="fmtm-text-lg fmtm-font-bold">Feature: {featureProperties?.osm_id}</h4>
          <div title="Close">
            <AssetModules.CloseIcon
              style={{ width: '20px' }}
              className="hover:fmtm-text-primaryRed fmtm-cursor-pointer"
              onClick={() => dispatch(ProjectActions.ToggleTaskModalStatus(false))}
            />
          </div>
        </div>
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
        {!submissionIds ||
          (submissionIds?.length !== 0 && (
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
                        <Button
                          btnText="validate this feature"
                          btnType="other"
                          className="fmtm-font-bold !fmtm-rounded fmtm-text-sm fmtm-flex fmtm-justify-center fmtm-uppercase !fmtm-w-fit md:!fmtm-w-full"
                        />
                      </Link>
                    </div>
                  ))}
                </>
              ) : (
                <Link to={`/project-submissions/${projectId}/tasks/${taskId}/submission/${submissionIds}`}>
                  <Button
                    btnText="validate this feature"
                    btnType="other"
                    className="fmtm-font-bold !fmtm-rounded fmtm-text-sm fmtm-flex fmtm-justify-center fmtm-uppercase fmtm-w-fit md:!fmtm-w-full fmtm-mx-auto"
                  />
                </Link>
              )}
            </div>
          ))}
      </div>
    </div>
  );
};

export default FeatureSelectionPopup;
