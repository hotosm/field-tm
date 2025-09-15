import React from 'react';
import { Loader2 } from 'lucide-react';
import AssetModules from '@/shared/AssetModules.js';
import CoreModules from '@/shared/CoreModules.js';
import { Modal } from '@/components/common/Modal';
import Button from '@/components/common/Button';
import { CustomSelect } from '@/components/common/Select.js';
import DateRangePicker from '@/components/common/DateRangePicker';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/common/Dropdown';
import { reviewStateData } from '@/constants/projectSubmissionsConstants';
import { task_event, task_state } from '@/types/enums';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { TaskActions } from '@/store/slices/TaskSlice';
import windowDimention from '@/hooks/WindowDimension';
import { useNavigate, useParams } from 'react-router-dom';
import { DownloadProjectSubmission } from '@/api/task';
import { CreateTaskEvent } from '@/api/TaskEvent';
import { useIsFetching } from '@tanstack/react-query';

const VITE_API_URL = import.meta.env.VITE_API_URL;

interface baseFilterType<T> {
  task_id: string | undefined;
  submitted_by: string | undefined;
  review_state: string | undefined;
  submitted_date_range: T;
  pageIndex: number;
  pageSize: number;
}

type tempFilterType = baseFilterType<{ start: Date | null; end: Date | null }>;
type filterType = baseFilterType<string | null>;

type filterPropsType = {
  toggleView: React.ReactElement;
  tempFilter: tempFilterType;
  setTempFilter: React.Dispatch<React.SetStateAction<tempFilterType>>;
  filter: Pick<filterType, 'task_id' | 'submitted_by' | 'review_state'> & {
    submitted_date_range: string | undefined;
  };
  applyFilter: any;
  clearFilters: any;
  refreshTable: any;
};

const Filter = ({
  toggleView,
  tempFilter,
  setTempFilter,
  filter,
  applyFilter,
  clearFilters,
  refreshTable,
}: filterPropsType) => {
  const dispatch = useAppDispatch();
  const { windowSize } = windowDimention();
  const params = useParams();
  const navigate = useNavigate();

  const projectId = params.projectId!;

  const isSubmissionFormFieldsFetching = useIsFetching({ queryKey: ['submission-form-fields', +projectId] });
  const isSubmissionTableDataFetching = useIsFetching({ queryKey: ['submission-table-data', filter] });

  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const josmEditorError = useAppSelector((state) => state.task.josmEditorError);
  const taskInfo = useAppSelector((state) => state.task.taskInfo);
  const updateTaskStatusLoading = useAppSelector((state) => state.common.loading);
  const downloadSubmissionLoading = useAppSelector((state) => state.task.downloadSubmissionLoading);
  const projectInfo = useAppSelector((state) => state.project.projectInfo);

  const submissionTableRefreshing = useAppSelector((state) => state.submission.submissionTableRefreshing);
  const projectData = useAppSelector((state) => state.project.projectTaskBoundries);
  const projectIndex = projectData.findIndex((project) => project.id == +projectId);
  const currentStatus = {
    ...projectData?.[projectIndex]?.taskBoundries?.filter((task) => {
      return tempFilter.task_id && task?.id === +tempFilter.task_id;
    })?.[0],
  };

  const submissionDownloadTypes: { type: 'csv' | 'json' | 'geojson'; label: string; loading: boolean }[] = [
    {
      type: 'csv',
      label: 'Download as Csv',
      loading: downloadSubmissionLoading.fileType === 'csv' && downloadSubmissionLoading.loading,
    },
    {
      type: 'json',
      label: 'Download as Json',
      loading: downloadSubmissionLoading.fileType === 'json' && downloadSubmissionLoading.loading,
    },
    {
      type: 'geojson',
      label: 'Download as GeoJson',
      loading: downloadSubmissionLoading.fileType === 'geojson' && downloadSubmissionLoading.loading,
    },
  ];

  const handleDownload = (downloadType: 'csv' | 'json' | 'geojson') => {
    dispatch(
      DownloadProjectSubmission(`${VITE_API_URL}/submission/download`, projectInfo.name!, {
        project_id: projectId,
        submitted_date_range: filter?.submitted_date_range,
        file_type: downloadType,
      }),
    );
  };

  const handleTaskMap = async () => {
    await dispatch(
      CreateTaskEvent(
        `${VITE_API_URL}/tasks/${currentStatus.id}/event`,
        task_event.GOOD,
        projectId!,
        tempFilter?.task_id || '',
        authDetails || {},
        { project_id: projectId },
      ),
    );
    navigate(`/project/${projectId}`);
  };

  const filterLength = Object.entries(filter).filter(
    ([key, value]) => ['task_id', 'submitted_by', 'review_state', 'submitted_date_range'].includes(key) && !!value,
  ).length;

  return (
    <div>
      {' '}
      <Modal
        className={`fmtm-w-[700px]`}
        description={
          <div>
            <h3 className="fmtm-text-lg fmtm-font-bold fmtm-mb-4">Connection with JOSM failed</h3>
            <p className="fmtm-text-lg">
              Please verify if JOSM is running on your computer and the remote control is enabled.
            </p>
          </div>
        }
        open={!!josmEditorError}
        onOpenChange={() => {
          dispatch(TaskActions.SetJosmEditorError(null));
        }}
      />
      <div className="fmtm-flex xl:fmtm-items-end xl:fmtm-justify-between fmtm-flex-col lg:fmtm-flex-row fmtm-gap-4 fmtm-mb-6">
        <div
          className={`${
            windowSize.width < 2000 ? 'fmtm-w-full md:fmtm-w-fit' : 'fmtm-w-fit'
          } fmtm-flex xl:fmtm-items-end fmtm-gap-2 xl:fmtm-gap-4 fmtm-rounded-lg fmtm-flex-col sm:fmtm-flex-row fmtm-order-2 md:-fmtm-order-1`}
        >
          <DropdownMenu modal={false}>
            <DropdownMenuTrigger>
              <Button variant="secondary-red">
                <AssetModules.TuneIcon style={{ fontSize: '20px' }} />
                FILTER{' '}
                <div className="fmtm-bg-primaryRed fmtm-text-white fmtm-rounded-full fmtm-w-4 fmtm-h-4 fmtm-flex fmtm-justify-center fmtm-items-center">
                  <p>{filterLength}</p>
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="fmtm-z-[50]" align="start">
              <div
                className={`fmtm-w-fit fmtm-max-w-[90vw] -fmtm-bottom-20 fmtm-bg-white fmtm-px-4 fmtm-rounded-lg fmtm-shadow-2xl fmtm-pb-4 fmtm-pt-2 fmtm-gap-4 fmtm-items-end fmtm-flex fmtm-flex-wrap`}
              >
                <div className={`${windowSize.width < 500 ? 'fmtm-w-full' : 'fmtm-w-[11rem]'}`}>
                  <CustomSelect
                    title="Task Id"
                    placeholder="Select"
                    data={taskInfo}
                    dataKey="value"
                    value={tempFilter?.task_id?.toString() || ''}
                    valueKey="task_id"
                    label="task_id"
                    onValueChange={(value) =>
                      value && setTempFilter((prev: filterType) => ({ ...prev, task_id: value.toString() }))
                    }
                    className="fmtm-text-grey-700 fmtm-text-sm !fmtm-mb-0 fmtm-bg-white"
                  />
                </div>
                <div className={`${windowSize.width < 500 ? 'fmtm-w-full' : 'fmtm-w-[11rem]'}`}>
                  <CustomSelect
                    title="Review State"
                    placeholder="Select"
                    data={reviewStateData}
                    dataKey="value"
                    value={tempFilter?.review_state || ''}
                    valueKey="value"
                    label="label"
                    onValueChange={(value) =>
                      value && setTempFilter((prev) => ({ ...prev, review_state: value.toString() }))
                    }
                    errorMsg=""
                    className="fmtm-text-grey-700 fmtm-text-sm !fmtm-mb-0 fmtm-bg-white"
                  />
                </div>
                <div className={`${windowSize.width < 500 ? 'fmtm-w-full' : 'fmtm-w-[12rem]'}`}>
                  <DateRangePicker
                    title="Submitted Date"
                    startDate={tempFilter.submitted_date_range?.start}
                    endDate={tempFilter.submitted_date_range?.end}
                    setStartDate={(date) =>
                      setTempFilter((prev) => ({
                        ...prev,
                        submitted_date_range: { ...prev.submitted_date_range, start: date },
                      }))
                    }
                    setEndDate={(date) =>
                      setTempFilter((prev) => ({
                        ...prev,
                        submitted_date_range: { ...prev.submitted_date_range, end: date },
                      }))
                    }
                    className="fmtm-text-grey-700 fmtm-text-sm !fmtm-mb-0 fmtm-w-full"
                  />
                </div>
                <div className={`${windowSize.width < 500 ? 'fmtm-w-full' : 'fmtm-w-[11rem]'}`}>
                  <p className={`fmtm-text-grey-700 fmtm-text-sm fmtm-font-semibold !fmtm-bg-transparent`}>
                    Submitted By
                  </p>
                  <div className="fmtm-border fmtm-border-gray-300 sm:fmtm-w-fit fmtm-flex fmtm-bg-white fmtm-items-center fmtm-px-1">
                    <input
                      type="search"
                      className="fmtm-h-[1.9rem] fmtm-p-2 fmtm-w-full fmtm-outline-none"
                      placeholder="Search User"
                      onChange={(e) => {
                        setTempFilter((prev) => ({ ...prev, submitted_by: e.target.value }));
                      }}
                    ></input>
                    <AssetModules.SearchIcon className="fmtm-text-[#9B9999] fmtm-cursor-pointer" />
                  </div>
                </div>
                <Button
                  variant="secondary-red"
                  onClick={applyFilter}
                  disabled={isSubmissionFormFieldsFetching > 0 || isSubmissionTableDataFetching > 0}
                >
                  Apply
                </Button>
                <Button
                  variant="secondary-red"
                  onClick={clearFilters}
                  disabled={isSubmissionFormFieldsFetching > 0 || isSubmissionTableDataFetching > 0}
                >
                  Reset
                </Button>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
          <div className="fmtm-flex fmtm-gap-4">
            <DropdownMenu>
              <DropdownMenuTrigger>
                <Button variant="link-grey">
                  <AssetModules.FileDownloadIcon className="!fmtm-text-xl" />
                  DOWNLOAD
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="fmtm-z-[5000] fmtm-bg-white">
                {submissionDownloadTypes?.map((submissionDownload) => (
                  <DropdownMenuItem
                    key={submissionDownload.type}
                    disabled={submissionDownload.loading}
                    onSelect={() => handleDownload(submissionDownload.type)}
                  >
                    <div className="fmtm-flex fmtm-gap-2 fmtm-items-center">
                      <p className="fmtm-text-base">{submissionDownload.label}</p>
                      {submissionDownload.loading && (
                        <Loader2 className="fmtm-h-4 fmtm-w-4 fmtm-animate-spin fmtm-text-primaryRed" />
                      )}
                    </div>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            <Button
              variant="link-grey"
              onClick={refreshTable}
              isLoading={
                (isSubmissionTableDataFetching > 0 || isSubmissionFormFieldsFetching > 0) && submissionTableRefreshing
              }
              disabled={isSubmissionTableDataFetching > 0 || isSubmissionFormFieldsFetching > 0}
            >
              <AssetModules.RefreshIcon className="!fmtm-text-xl" />
              REFRESH
            </Button>
          </div>
        </div>
        <div className="fmtm-w-full fmtm-flex fmtm-items-center fmtm-justify-end xl:fmtm-w-fit fmtm-gap-3">
          {tempFilter?.task_id &&
            projectData?.[projectIndex]?.taskBoundries?.find((task) => task?.id === +tempFilter?.task_id)
              ?.task_state === task_state.LOCKED_FOR_VALIDATION && (
              <Button variant="primary-red" onClick={handleTaskMap} isLoading={updateTaskStatusLoading}>
                MARK AS VALIDATED
              </Button>
            )}
          {toggleView}
        </div>
      </div>
    </div>
  );
};

export default Filter;
