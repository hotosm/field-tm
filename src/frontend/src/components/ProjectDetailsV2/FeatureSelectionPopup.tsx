// Popup used to display task feature info & link to ODK Collect

import React from 'react';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import Button from '@/components/common/Button';
import { ProjectActions } from '@/store/slices/ProjectSlice';

type TaskFeatureSelectionProperties = {
  osm_id: number;
  tags: string;
  timestamp: string;
  version: number;
  changeset: number;
};

type TaskFeatureSelectionPopupPropType = {
  featureProperties: TaskFeatureSelectionProperties | null;
};

const TaskFeatureSelectionPopup = ({ featureProperties }: TaskFeatureSelectionPopupPropType) => {
  const dispatch = CoreModules.useAppDispatch();
  const taskModalStatus = CoreModules.useAppSelector((state) => state.project.taskModalStatus);
  const projectInfo = CoreModules.useAppSelector((state) => state.project.projectInfo);
  const entityOsmMap = CoreModules.useAppSelector((state) => state.project.entityOsmMap);
  return (
    <div
      className={`fmtm-duration-1000 fmtm-z-[10002] fmtm-h-fit ${
        taskModalStatus
          ? 'fmtm-bottom-[4.4rem] md:fmtm-top-[50%] md:-fmtm-translate-y-[35%] fmtm-right-0 fmtm-w-[100vw] md:fmtm-w-[50vw] md:fmtm-max-w-[25rem]'
          : 'fmtm-top-[calc(100vh)] md:fmtm-top-[calc(40vh)] md:fmtm-left-[calc(100vw)] fmtm-w-[100vw]'
      } fmtm-fixed
        fmtm-rounded-t-3xl fmtm-border-opacity-50`}
    >
      <div
        className={`fmtm-absolute fmtm-top-[17px] fmtm-right-[20px] ${
          taskModalStatus ? '' : 'fmtm-hidden'
        }  fmtm-cursor-pointer fmtm-flex fmtm-items-center fmtm-gap-3`}
      >
        <div title="Close">
          <AssetModules.CloseIcon
            style={{ width: '20px' }}
            className="hover:fmtm-text-primaryRed"
            onClick={() => dispatch(ProjectActions.ToggleTaskModalStatus(false))}
          />
        </div>
      </div>
      <div
        className={`fmtm-bg-[#fbfbfb] ${
          taskModalStatus ? 'sm:fmtm-shadow-[-20px_0px_60px_25px_rgba(0,0,0,0.2)] fmtm-border-b sm:fmtm-border-b-0' : ''
        } fmtm-rounded-t-2xl md:fmtm-rounded-tr-none md:fmtm-rounded-l-2xl`}
      >
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-2 fmtm-p-3 sm:fmtm-p-5">
          <h4 className="fmtm-text-lg fmtm-font-bold">Feature: {featureProperties?.osm_id}</h4>
        </div>

        <div className="fmtm-h-fit fmtm-p-2 sm:fmtm-p-5 fmtm-border-t">
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-1 fmtm-mt-1">
            <p>
              <span className="fmtm-font-semibold">Tags: </span>
              <span className="fmtm-text-primaryRed fmtm-overflow-hidden fmtm-line-clamp-2">
                {featureProperties?.tags}
              </span>
            </p>
            <p>
              <span className="fmtm-font-semibold">Timestamp: </span>
              <span className="fmtm-text-primaryRed">{featureProperties?.timestamp}</span>
            </p>
            <p>
              <span className="fmtm-font-semibold">Changeset: </span>
              <span className="fmtm-text-primaryRed">{featureProperties?.changeset}</span>
            </p>
            <p>
              <span className="fmtm-font-semibold">Version: </span>
              <span className="fmtm-text-primaryRed">{featureProperties?.version}</span>
            </p>
          </div>
        </div>

        <div className="fmtm-p-2 sm:fmtm-p-5 fmtm-border-t">
          <Button
            btnText="MAP FEATURE IN ODK"
            btnType="primary"
            type="submit"
            className="fmtm-font-bold !fmtm-rounded fmtm-text-sm !fmtm-py-2 !fmtm-w-full fmtm-flex fmtm-justify-center"
            onClick={() => {
              // XForm name is constructed from lower case project title with underscores
              const projectName = projectInfo.title.toLowerCase().split(' ').join('_');
              const projectCategory = projectInfo.xform_category;
              const formName = `${projectName}_${projectCategory}`;

              const entity = entityOsmMap.find((x) => x.osm_id === featureProperties?.osm_id);
              const entityUuid = entity ? entity.id : null;

              if (!formName || !entityUuid) {
                return;
              }

              document.location.href = `odkcollect://form/${formName}?existing=${entityUuid}`;
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default TaskFeatureSelectionPopup;
