import CoreModules from '@/shared/CoreModules.js';
import React, { useEffect } from 'react';
import { SubmissionService, GetSubmissionPhotosService } from '@/api/Submission';
import SubmissionInstanceMap from '@/components/SubmissionMap/SubmissionInstanceMap';
import { GetSubmissionDashboard } from '@/api/Project';
import Button from '@/components/common/Button';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';
import UpdateReviewStatusModal from '@/components/ProjectSubmissions/UpdateReviewStatusModal';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { useNavigate } from 'react-router-dom';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import Accordion from '@/components/common/Accordion';
import { GetProjectComments } from '@/api/Project';
import SubmissionComments from '@/components/SubmissionInstance/SubmissionComments';
import { extractGeojsonFromObject } from '@/utilfunctions/extractGeojsonFromObject';
import { project_status, submission_status } from '@/types/enums';
import { useIsOrganizationAdmin, useIsProjectManager } from '@/hooks/usePermissions';

function removeNullValues(obj: Record<string, any>) {
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

const SubmissionDetails = () => {
  useDocumentTitle('Submission Instance');
  const dispatch = useAppDispatch();
  const params = CoreModules.useParams();
  const navigate = useNavigate();

  const projectId = params.projectId;
  const paramsInstanceId = params.instanceId;
  const taskUid = params.taskId;
  const projectDashboardDetail = useAppSelector((state) => state.project.projectDashboardDetail);
  const projectDashboardLoading = useAppSelector((state) => state.project.projectDashboardLoading);
  const submissionDetails = useAppSelector((state) => state.submission.submissionDetails);
  const submissionDetailsLoading = useAppSelector((state) => state.submission.submissionDetailsLoading);
  const taskId = submissionDetails?.task_id ? submissionDetails?.task_id : '-';
  const submissionPhotosLoading = useAppSelector((state) => state.submission.submissionPhotosLoading);
  const submissionPhotos = useAppSelector((state) => state.submission.submissionPhotos);

  const isProjectManager = useIsProjectManager(projectId as string);
  const isOrganizationAdmin = useIsOrganizationAdmin(projectDashboardDetail?.organisation_id as number);

  const { start, end, today, deviceid, new_feature, ...restSubmissionDetails } = submissionDetails || {};
  const dateDeviceDetails = { start, end, today, deviceid };

  const renderValue = (value: any, key: string = '') => {
    if (key === 'start' || key === 'end') {
      return (
        <>
          <div className="fmtm-capitalize fmtm-text-base fmtm-font-bold fmtm-text-[#555]">{key}</div>
          <p className="fmtm-text-sm fmtm-text-[#555]">
            {value?.split('T')[0]}, {value?.split('T')[1]}
          </p>
        </>
      );
    } else if (typeof value === 'object' && value !== null && Object.values(value).includes('Point')) {
      return (
        <>
          {renderValue(
            `${value?.type} (${value?.coordinates?.[0]},${value?.coordinates?.[1]},${value?.coordinates?.[2]}`,
            key,
          )}
          <div className="fmtm-border-b fmtm-my-3" />
          {renderValue(value?.properties?.accuracy, 'accuracy')}
        </>
      );
    } else if (typeof value === 'object' && value !== null) {
      return (
        <ul className="fmtm-flex fmtm-flex-col fmtm-gap-1">
          <Accordion
            className="fmtm-rounded-xl fmtm-px-6"
            onToggle={() => {}}
            hasSeperator={false}
            header={<p className="fmtm-text-xl fmtm-text-[#555]">{key}</p>}
            body={
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
                {Object.entries(value).map(([key, nestedValue]) => {
                  return <div key={key}>{renderValue(nestedValue, key)}</div>;
                })}
              </div>
            }
          />
        </ul>
      );
    } else {
      return (
        <>
          <div className="fmtm-capitalize fmtm-text-base fmtm-font-bold fmtm-leading-normal fmtm-text-[#555] fmtm-break-words">
            {key}
          </div>
          {typeof value === 'string' && /\.(jpeg|jpg|png|gif|bmp|webp|svg|tiff?|heic|avif)$/i.test(value) ? (
            submissionPhotosLoading ? (
              <CoreModules.Skeleton style={{ width: '16rem', height: '8rem' }} className="!fmtm-rounded-lg" />
            ) : (
              <img src={submissionPhotos[value]} alt={key} className="fmtm-max-w-[16rem]" />
            )
          ) : (
            <span className="fmtm-text-sm fmtm-text-[#555] fmtm-break-words">{value}</span>
          )}
        </>
      );
    }
  };

  useEffect(() => {
    dispatch(GetSubmissionDashboard(`${import.meta.env.VITE_API_URL}/submission/${projectId}/dashboard`));
  }, []);

  useEffect(() => {
    dispatch(
      SubmissionService(`${import.meta.env.VITE_API_URL}/submission/${paramsInstanceId}?project_id=${projectId}`),
    );
  }, [projectId, paramsInstanceId]);

  useEffect(() => {
    // Note here taskUid is coerced to string so we have to check that
    if (taskUid == 'undefined') return;
    dispatch(
      GetProjectComments(
        `${import.meta.env.VITE_API_URL}/tasks/${parseInt(taskUid)}/history?project_id=${projectId}&comments=true`,
      ),
    );
  }, [taskUid]);

  useEffect(() => {
    if (paramsInstanceId) {
      dispatch(
        GetSubmissionPhotosService(`${import.meta.env.VITE_API_URL}/submission/${paramsInstanceId}/photos`, {
          project_id: projectId,
        }),
      );
    }
  }, [paramsInstanceId]);

  const filteredData = restSubmissionDetails ? removeNullValues(restSubmissionDetails) : {};

  return (
    <>
      <UpdateReviewStatusModal />
      <div className="fmtm-bg-[#F5F5F5] fmtm-box-border">
        {projectDashboardLoading ? (
          <CoreModules.Skeleton style={{ width: '250px' }} className="fmtm-mb-4" />
        ) : (
          <div className="fmtm-pb-4">
            <p className="fmtm-text-[#706E6E] fmtm-text-base">
              <span
                className="hover:fmtm-text-primaryRed fmtm-cursor-pointer fmtm-duration-200"
                onClick={() => navigate(`/project/${projectId}`)}
              >
                {projectDashboardDetail?.slug}
              </span>
              <span> &gt; </span>
              <span
                className="hover:fmtm-text-primaryRed fmtm-cursor-pointer fmtm-duration-200"
                onClick={() => navigate(`/project-submissions/${projectId}?tab=table`)}
              >
                Dashboard
              </span>
              <span> &gt; </span>
              <span className="fmtm-text-black">Submissions</span>
            </p>
          </div>
        )}
        <div className="fmtm-grid fmtm-grid-cols-1 md:fmtm-grid-cols-2 fmtm-gap-x-8">
          <div>
            <div>
              {projectDashboardLoading ? (
                <CoreModules.Skeleton className="md:!fmtm-w-full fmtm-h-[9rem]" />
              ) : (
                <div className="fmtm-bg-white fmtm-rounded-lg fmtm-w-full fmtm-h-fit fmtm-p-2 fmtm-px-4 md:fmtm-py-5 md:fmtm-shadow-[0px_10px_20px_0px_rgba(96,96,96,0.1)] fmtm-flex fmtm-flex-col">
                  <h2 className="fmtm-text-base fmtm-text-[#545454] fmtm-font-bold fmtm-mb-4 fmtm-break-words">
                    {projectDashboardDetail?.slug}
                  </h2>
                  <h2 className="fmtm-text-base fmtm-font-bold fmtm-text-[#545454]">Task: {taskId}</h2>
                  <h2 className="fmtm-text-base fmtm-font-bold fmtm-text-[#545454] fmtm-break-words">
                    Submission Id: {paramsInstanceId}
                  </h2>
                  <h2 className="fmtm-text-base fmtm-font-bold fmtm-text-[#545454] fmtm-break-words">
                    Submission Status: {submission_status[restSubmissionDetails?.__system?.reviewState]}
                  </h2>
                </div>
              )}
              {!projectDashboardLoading &&
                (isProjectManager || isOrganizationAdmin) &&
                projectDashboardDetail?.status === project_status.PUBLISHED && (
                  <div className="fmtm-mt-8">
                    <Button
                      variant="primary-red"
                      onClick={() => {
                        dispatch(
                          SubmissionActions.SetUpdateReviewStatusModal({
                            toggleModalStatus: true,
                            instanceId: paramsInstanceId,
                            projectId: projectId,
                            taskId: taskId,
                            reviewState: restSubmissionDetails?.__system?.reviewState,
                            taskUid: taskUid,
                            entity_id: restSubmissionDetails?.feature,
                            label: restSubmissionDetails?.meta?.entity?.label,
                          }),
                        );
                      }}
                      disabled={submissionDetailsLoading}
                    >
                      Update Review Status
                    </Button>
                  </div>
                )}
            </div>

            {/* start, end, today, deviceid values */}
            {submissionDetailsLoading ? (
              <div className="fmtm-grid fmtm-grid-cols-2 fmtm-mt-6 fmtm-gap-0">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="fmtm-border-b fmtm-py-3">
                    <CoreModules.Skeleton key={i} className="fmtm-h-[51px] !fmtm-w-[90%]" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="fmtm-grid fmtm-grid-cols-2 fmtm-mt-6">
                {Object.entries(dateDeviceDetails).map(([key, value]) => (
                  <div key={key}>
                    <div className="fmtm-border-b fmtm-border-[#e2e2e2] fmtm-py-3">{renderValue(value, key)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="fmtm-flex fmtm-flex-grow fmtm-justify-center fmtm-mt-10 md:fmtm-mt-0">
            <div className="fmtm-w-full fmtm-h-[20rem] md:fmtm-h-full fmtm-rounded-lg fmtm-overflow-hidden">
              <SubmissionInstanceMap featureGeojson={extractGeojsonFromObject(restSubmissionDetails)} />
            </div>
          </div>
        </div>
        <div className="fmtm-grid fmtm-grid-cols-1 md:fmtm-grid-cols-2 fmtm-gap-x-8 fmtm-mt-10 fmtm-gap-y-10 fmtm-mb-5">
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
                  <div className="fmtm-border-b fmtm-border-[#e2e2e2] fmtm-py-3">{renderValue(value, key)}</div>
                </div>
              ))}
            </div>
          )}
          <div>
            <SubmissionComments />
          </div>
        </div>
      </div>
    </>
  );
};

export default SubmissionDetails;
