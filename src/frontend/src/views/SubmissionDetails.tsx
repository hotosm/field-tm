import CoreModules from '@/shared/CoreModules.js';
import React, { useEffect } from 'react';
import environment from '@/environment';
import { SubmissionService } from '@/api/Submission';
import SubmissionInstanceMap from '@/components/SubmissionMap/SubmissionInstanceMap';
import { GetProjectDashboard } from '@/api/Project';
import Button from '@/components/common/Button';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';
import UpdateReviewStatusModal from '@/components/ProjectSubmissions/UpdateReviewStatusModal';
import { useAppSelector } from '@/types/reduxTypes';

const SubmissionDetails = () => {
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const encodedProjectId = params.projectId;
  const decodedProjectId = environment.decode(encodedProjectId);
  const taskId = params.taskId;
  const paramsInstanceId = params.instanceId;
  const projectDashboardDetail = CoreModules.useAppSelector((state) => state.project.projectDashboardDetail);
  const projectDashboardLoading = CoreModules.useAppSelector((state) => state.project.projectDashboardLoading);

  const submissionDetails = useAppSelector((state) => state.submission.submissionDetails);
  const submissionDetailsLoading = useAppSelector((state) => state.submission.submissionDetailsLoading);

  useEffect(() => {
    dispatch(GetProjectDashboard(`${import.meta.env.VITE_API_URL}/projects/project_dashboard/${decodedProjectId}`));
  }, []);

  useEffect(() => {
    dispatch(
      SubmissionService(
        `${
          import.meta.env.VITE_API_URL
        }/submission/task_submissions/${decodedProjectId}?task_id=${taskId}&submission_id=${paramsInstanceId}`,
      ),
    );
  }, [decodedProjectId, taskId, paramsInstanceId]);

  function removeNullValues(obj) {
    const newObj = {};
    for (const [key, value] of Object.entries(obj)) {
      if (value !== null) {
        if (typeof value === 'object') {
          const nestedObj = removeNullValues(value);
          if (Object.keys(nestedObj).length > 0) {
            newObj[key] = nestedObj;
          }
        } else {
          newObj[key] = value;
        }
      }
    }
    return newObj;
  }
  const filteredData = submissionDetails ? removeNullValues(submissionDetails) : {};

  var coordinatesArray = submissionDetails?.all?.xlocation?.split(';').map(function (coord) {
    let coordinate = coord
      .trim()
      .split(' ')
      .slice(0, 2)
      .map((value) => {
        return parseFloat(value);
      });
    return [coordinate[1], coordinate[0]];
  });

  const geojsonFeature = {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: coordinatesArray,
        },
        properties: {},
      },
    ],
  };

  const renderValue = (value, key = '') => {
    if (key === 'start' || key === 'end') {
      return (
        <p>
          {value?.split('T')[0]}, {value?.split('T')[1]}
        </p>
      );
    } else if (typeof value === 'object' && Object.values(value).includes('Point')) {
      return (
        <div>
          <p className="fmtm-capitalize"></p> {value?.type} ({value?.coordinates?.[0]},{value?.coordinates?.[1]},
          {value?.coordinates?.[2]}){renderValue(value?.properties)}
        </div>
      );
    } else if (typeof value === 'object') {
      return (
        <ul className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          {Object.entries(value).map(([key, nestedValue]) => (
            <CoreModules.Box sx={{ textTransform: 'capitalize' }} key={key}>
              <span color="error" className="fmtm-font-bold">
                {key}:{' '}
              </span>
              {renderValue(nestedValue, key)}
            </CoreModules.Box>
          ))}
        </ul>
      );
    } else {
      return <span>{value}</span>;
    }
  };

  return (
    <div className="fmtm-bg-gray-100 fmtm-box-border fmtm-border-[1px] fmtm-border-t-white fmtm-border-t-[0px] fmtm-px-[1.5rem] md:fmtm-px-[3.5rem] fmtm-py-[1.5rem] md:fmtm-py-[2rem]">
      <UpdateReviewStatusModal />
      <div className="fmtm-flex fmtm-flex-col xl:fmtm-flex-row">
        <div>
          {projectDashboardLoading ? (
            <CoreModules.Skeleton className="md:!fmtm-w-[35rem] fmtm-h-[8.5rem]" />
          ) : (
            <div className="fmtm-bg-white fmtm-rounded-lg fmtm-w-full md:fmtm-w-[35rem] fmtm-h-fit fmtm-p-2 fmtm-px-4 md:fmtm-p-4 md:fmtm-shadow-[0px_10px_20px_0px_rgba(96,96,96,0.1)] fmtm-flex fmtm-flex-col">
              <h2 className="fmtm-text-2xl fmtm-text-[#545454] fmtm-font-bold fmtm-mb-4">
                {projectDashboardDetail?.project_name_prefix}
              </h2>
              <h2 className="fmtm-text-xl fmtm-font-bold fmtm-text-[#545454]">Task: {taskId}</h2>
              <h2 className="fmtm-text-lg fmtm-font-bold fmtm-text-[#545454]">Submission Id: {paramsInstanceId}</h2>
            </div>
          )}
          <Button
            btnText="Update Review Status"
            btnType="primary"
            className="fmtm-w-fit fmtm-justify-center !fmtm-rounded fmtm-font-bold fmtm-text-sm !fmtm-py-2 fmtm-mt-8"
            onClick={() => {
              dispatch(
                SubmissionActions.SetUpdateReviewStatusModal({
                  toggleModalStatus: true,
                  submissionId: paramsInstanceId,
                }),
              );
            }}
          />
        </div>
        <div className="fmtm-flex fmtm-flex-grow fmtm-justify-center">
          <div className="fmtm-w-full fmtm-my-10 xl:fmtm-my-0 xl:fmtm-w-[500px] 2xl:fmtm-w-[700px] fmtm-h-[300px] fmtm-rounded-lg fmtm-overflow-hidden">
            <SubmissionInstanceMap featureGeojson={geojsonFeature} />
          </div>
        </div>
      </div>
      {submissionDetailsLoading ? (
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-3 fmtm-mt-5">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="fmtm-border-b-[1px] fmtm-pb-4">
              <CoreModules.Skeleton key={i} className="fmtm-h-[100px]" />
            </div>
          ))}
        </div>
      ) : (
        <div>
          {Object.entries(filteredData).map(([key, value]) => (
            <div key={key}>
              <CoreModules.Box sx={{ borderBottom: '1px solid #e2e2e2', padding: '8px' }}>
                <div className="fmtm-capitalize fmtm-text-xl fmtm-font-bold fmtm-mb-1">{key}</div>
                {renderValue(value, key)}
              </CoreModules.Box>
            </div>
          ))}{' '}
        </div>
      )}
    </div>
  );
};

export default SubmissionDetails;
