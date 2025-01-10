import React, { useEffect } from 'react';
import ConflationMap from '@/components/DataConflation/ConflationMap';
import TaskInfo from '@/components/DataConflation/TaskInfo';
import SubmissionConflation from '@/components/DataConflation/SubmissionConflation';
import { SubmissionConflationGeojsonService } from '@/api/DataConflation';
import { useParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';

const DataConflation = () => {
  const dispatch = useAppDispatch();
  const { projectId, taskId } = useParams();
  const selectedFeatureOSMId = useAppSelector((state) => state.dataconflation.selectedFeatureOSMId);

  useEffect(() => {
    dispatch(
      SubmissionConflationGeojsonService(
        `${
          import.meta.env.VITE_API_URL
        }/submission/conflate-submission-geojson?project_id=${projectId}&task_id=${taskId}`,
      ),
    );
  }, []);

  return (
    <div className="fmtm-bg-[#F5F5F5] md:fmtm-h-full fmtm-relative fmtm-p-5">
      <div className="fmtm-w-full fmtm-flex fmtm-gap-5 fmtm-flex-col lg:fmtm-flex-row md:fmtm-h-full">
        <div className="2xl:fmtm-w-[20%] lg:fmtm-h-full">
          <TaskInfo />
        </div>
        <div className="md:fmtm-h-[calc(100%-240px)] lg:fmtm-h-full fmtm-flex fmtm-flex-col md:fmtm-flex-row fmtm-gap-5 fmtm-w-full lg:fmtm-w-[80%]">
          <div
            className={`fmtm-h-[50vh] fmtm-w-full md:fmtm-h-full fmtm-duration-200 ${
              selectedFeatureOSMId ? 'md:fmtm-w-[65%]' : 'md:fmtm-w-full'
            }`}
          >
            <ConflationMap />
          </div>
          {selectedFeatureOSMId && (
            <div className="fmtm-w-full md:fmtm-h-full md:fmtm-w-[35%] fmtm-duration-200">
              <SubmissionConflation />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DataConflation;
