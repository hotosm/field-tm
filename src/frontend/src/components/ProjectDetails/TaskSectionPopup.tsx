import React from 'react';
import CoreModules from '../../shared/CoreModules';
import AssetModules from '../../shared/AssetModules';
import { ProjectActions } from '../../store/slices/ProjectSlice';

const TaskSectionPopup = ({ body }) => {
  const dispatch = CoreModules.useAppDispatch();
  const taskModalStatus = CoreModules.useAppSelector((state) => state.project.taskModalStatus);

  return (
    <div
      className={`fmtm-z-[3000]  fmtm-duration-1000  ${
        taskModalStatus
          ? 'fmtm-bottom-0 fmtm-right-0 md:fmtm-bottom-[calc(20vh)] fmtm-w-[100vw] md:fmtm-w-[50vw] md:fmtm-max-w-[25rem]'
          : 'fmtm-top-[calc(100vh)] md:fmtm-top-[calc(50vh)] md:fmtm-left-[calc(100vw)] fmtm-w-[100vw]'
      } fmtm-fixed
        fmtm-rounded-t-3xl fmtm-border-opacity-50`}
    >
      <div
        onClick={() => dispatch(ProjectActions.ToggleTaskModalStatus(false))}
        className={`fmtm-absolute fmtm-top-[17px] fmtm-right-[20px] ${
          taskModalStatus ? '' : 'fmtm-hidden'
        }  fmtm-cursor-pointer`}
      >
        <AssetModules.CloseIcon />
      </div>
      <div className="fmtm-bg-[#fbfbfb] fmtm-p-5 fmtm-rounded-t-2xl fmtm-shadow-[-20px_0px_60px_25px_rgba(0,0,0,0.2)]  md:fmtm-rounded-tr-none md:fmtm-rounded-l-2xl">
        {body}
      </div>
    </div>
  );
};

export default TaskSectionPopup;
