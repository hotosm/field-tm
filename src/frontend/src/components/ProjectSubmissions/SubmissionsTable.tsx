import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import { Tooltip } from '@mui/material';
import { Loader2 } from 'lucide-react';

import AssetModules from '@/shared/AssetModules.js';
import CoreModules from '@/shared/CoreModules.js';
import windowDimention from '@/hooks/WindowDimension';

import Button from '@/components/common/Button';
import { Modal } from '@/components/common/Modal';
import { CustomSelect } from '@/components/common/Select.js';
import DateRangePicker from '@/components/common/DateRangePicker';
import Table, { TableHeader } from '@/components/common/CustomTable';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/common/Dropdown';
import UpdateReviewStatusModal from '@/components/ProjectSubmissions/UpdateReviewStatusModal';
import { reviewStateData } from '@/constants/projectSubmissionsConstants';

import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { task_state, task_event, project_status } from '@/types/enums';
import { filterType } from '@/store/types/ISubmissions';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';

import { CreateTaskEvent } from '@/api/TaskEvent';
import { ConvertXMLToJOSM, DownloadProjectSubmission } from '@/api/task';
import { SubmissionFormFieldsService, SubmissionTableService } from '@/api/SubmissionService';

import filterParams from '@/utilfunctions/filterParams';
import { camelToFlat } from '@/utilfunctions/commonUtils';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import SubmissionsTableSkeleton from '@/components/Skeletons/ProjectSubmissions.tsx/SubmissionsTableSkeleton';
import { useIsOrganizationAdmin, useIsProjectManager } from '@/hooks/usePermissions';

const VITE_API_URL = import.meta.env.VITE_API_URL;

const SubmissionsTable = ({ toggleView }) => {
  useDocumentTitle('Submission Table');
  const [searchParams, setSearchParams] = useSearchParams();

  const initialFilterState: filterType = {
    task_id: searchParams.get('task_id') ? searchParams?.get('task_id') || null : null,
    submitted_by: searchParams.get('submitted_by'),
    review_state: searchParams.get('review_state'),
    submitted_date_range: searchParams.get('submitted_date_range'),
  };
  const [filter, setFilter] = useState<filterType>(initialFilterState);

  const { windowSize } = windowDimention();
  const dispatch = useAppDispatch();
  const params = CoreModules.useParams();
  const navigate = useNavigate();

  const projectId = params.projectId;
  const submissionFormFields = useAppSelector((state) => state.submission.submissionFormFields);
  const submissionTableData = useAppSelector((state) => state.submission.submissionTableData);
  const submissionFormFieldsLoading = useAppSelector((state) => state.submission.submissionFormFieldsLoading);
  const submissionTableDataLoading = useAppSelector((state) => state.submission.submissionTableDataLoading);
  const submissionTableRefreshing = useAppSelector((state) => state.submission.submissionTableRefreshing);
  const taskInfo = useAppSelector((state) => state.task.taskInfo);
  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const josmEditorError = useAppSelector((state) => state.task.josmEditorError);
  const downloadSubmissionLoading = useAppSelector((state) => state.task.downloadSubmissionLoading);
  const authDetails = CoreModules.useAppSelector((state) => state.login.authDetails);
  const updateTaskStatusLoading = useAppSelector((state) => state.common.loading);

  const projectData = useAppSelector((state) => state.project.projectTaskBoundries);
  const projectIndex = projectData.findIndex((project) => project.id == +projectId);
  const currentStatus = {
    ...projectData?.[projectIndex]?.taskBoundries?.filter((task) => {
      return filter.task_id && task?.id === +filter.task_id;
    })?.[0],
  };
  const taskList = projectData[projectIndex]?.taskBoundries;

  const isProjectManager = useIsProjectManager(projectId as string);
  const isOrganizationAdmin = useIsOrganizationAdmin(projectInfo.organisation_id as null | number);

  const [paginationPage, setPaginationPage] = useState<number>(1);
  const [submittedBy, setSubmittedBy] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<{ start: Date | null; end: Date | null }>({
    start: initialFilterState?.submitted_date_range
      ? new Date(initialFilterState.submitted_date_range.split(',')[0])
      : null,
    end: initialFilterState?.submitted_date_range
      ? new Date(initialFilterState.submitted_date_range.split(',')[1])
      : null,
  });

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

  useEffect(() => {
    if (!dateRange.start || !dateRange.end) return;

    setFilter((prev) => ({
      ...prev,
      submitted_date_range: `${format(new Date(dateRange.start as Date), 'yyyy-MM-dd')},${format(new Date(dateRange.end as Date), 'yyyy-MM-dd')}`,
    }));
  }, [dateRange]);

  const updatedSubmissionFormFields = submissionFormFields
    //filter necessary fields only
    ?.filter(
      (formField) =>
        formField?.path.startsWith('/survey_questions') ||
        ['/start', '/end', '/username', '/task_id', '/status'].includes(formField?.path),
    )
    // convert path to dot notation & update name
    ?.map((formField) => {
      if (formField.type !== 'structure') {
        return {
          ...formField,
          path: formField?.path.slice(1).replace(/\//g, '.'),
          name: formField?.name.charAt(0).toUpperCase() + formField?.name.slice(1).replace(/_/g, ' '),
        };
      }
      return null;
    });

  useEffect(() => {
    dispatch(
      SubmissionTableService(`${VITE_API_URL}/submission/submission-table?project_id=${projectId}`, {
        page: paginationPage,
        ...filter,
      }),
    );
  }, [filter, paginationPage]);

  useEffect(() => {
    setPaginationPage(1);
  }, [filter]);

  const refreshTable = () => {
    dispatch(SubmissionFormFieldsService(`${VITE_API_URL}/submission/submission-form-fields?project_id=${projectId}`));
    dispatch(SubmissionActions.SetSubmissionTableRefreshing(true));
    dispatch(
      SubmissionTableService(`${VITE_API_URL}/submission/submission-table?project_id=${projectId}`, {
        page: paginationPage,
        ...filter,
      }),
    );
  };

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (submittedBy != null) {
        setFilter((prev) => ({ ...prev, submitted_by: submittedBy }));
      }
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [submittedBy, 500]);

  const handleChangePage = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | React.KeyboardEvent<HTMLInputElement>,
    newPage: number,
  ) => {
    if (!submissionTableData?.pagination?.pages) return;
    if (newPage + 1 > submissionTableData?.pagination?.pages || newPage + 1 < 1) {
      setPaginationPage(paginationPage);
      return;
    }
    setPaginationPage(newPage + 1);
  };

  const clearFilters = () => {
    setSearchParams({ tab: 'table' });
    setFilter({ task_id: null, submitted_by: null, review_state: null, submitted_date_range: null });
    setDateRange({ start: null, end: null });
  };

  function getValueByPath(obj: any, path: string) {
    let value = obj;
    path?.split('.')?.map((item) => {
      if (path === 'start' || path === 'end') {
        // start & end date is static
        value = `${value[item]?.split('T')[0]} ${value[item]?.split('T')[1]}`;
      } else if (
        value &&
        value[item] &&
        typeof value[item] === 'object' &&
        Object.values(value[item]).includes('Point')
      ) {
        // if the object values contains 'Point' as type
        value = `${value[item].type} (${value[item].coordinates})`;
      } else {
        if (!value || !item) {
          value = '';
          return;
        }
        value = value?.[item];
      }
    });
    return value ? (typeof value === 'object' ? '-' : value) : '-';
  }

  // const uploadToJOSM = () => {
  //   dispatch(ConvertXMLToJOSM(`${VITE_API_URL}/submission/get_osm_xml/${projectId}`, projectInfo?.outline?.bbox));
  // };

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
        projectId,
        filter?.task_id || '',
        authDetails || {},
        { project_id: projectId },
      ),
    );
    navigate(`/project/${projectId}`);
  };

  useEffect(() => {
    const filteredParams = filterParams(filter);
    setSearchParams({ tab: 'table', ...filteredParams });
  }, [filter]);

  return (
    <div className="">
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
          dispatch(CoreModules.TaskActions.SetJosmEditorError(null));
        }}
      />
      <UpdateReviewStatusModal />
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
                  <p>{Object.values(filter).filter((filterObjValue) => filterObjValue).length}</p>
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
                    value={filter?.task_id?.toString() || ''}
                    valueKey="task_id"
                    label="task_id"
                    onValueChange={(value) => value && setFilter((prev) => ({ ...prev, task_id: value.toString() }))}
                    className="fmtm-text-grey-700 fmtm-text-sm !fmtm-mb-0 fmtm-bg-white"
                  />
                </div>
                <div className={`${windowSize.width < 500 ? 'fmtm-w-full' : 'fmtm-w-[11rem]'}`}>
                  <CustomSelect
                    title="Review State"
                    placeholder="Select"
                    data={reviewStateData}
                    dataKey="value"
                    value={filter?.review_state || ''}
                    valueKey="value"
                    label="label"
                    onValueChange={(value) =>
                      value && setFilter((prev) => ({ ...prev, review_state: value.toString() }))
                    }
                    errorMsg=""
                    className="fmtm-text-grey-700 fmtm-text-sm !fmtm-mb-0 fmtm-bg-white"
                  />
                </div>
                <div className={`${windowSize.width < 500 ? 'fmtm-w-full' : 'fmtm-w-[12rem]'}`}>
                  <DateRangePicker
                    title="Submitted Date"
                    startDate={dateRange?.start}
                    endDate={dateRange?.end}
                    setStartDate={(date) => setDateRange((prev) => ({ ...prev, start: date }))}
                    setEndDate={(date) => setDateRange((prev) => ({ ...prev, end: date }))}
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
                        setSubmittedBy(e.target.value);
                      }}
                    ></input>
                    <AssetModules.SearchIcon className="fmtm-text-[#9B9999] fmtm-cursor-pointer" />
                  </div>
                </div>
                <Button
                  variant="secondary-red"
                  onClick={clearFilters}
                  disabled={submissionTableDataLoading || submissionFormFieldsLoading}
                >
                  Reset Filter
                </Button>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
          <div className="fmtm-flex fmtm-gap-2">
            {/* comment out button until JOSM is implemented */}
            {/* <Button variant="primary-red" onClick={uploadToJOSM}>
              <AssetModules.FileDownloadIcon className="!fmtm-text-xl" />
              UPLOAD TO JOSM
            </Button> */}
            <DropdownMenu>
              <DropdownMenuTrigger>
                <Button variant="primary-red">
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
              variant="primary-red"
              onClick={refreshTable}
              isLoading={(submissionTableDataLoading || submissionFormFieldsLoading) && submissionTableRefreshing}
              disabled={submissionTableDataLoading || submissionFormFieldsLoading}
            >
              <AssetModules.ReplayIcon className="!fmtm-text-xl" />
              REFRESH
            </Button>
          </div>
        </div>
        <div className="fmtm-w-full fmtm-flex fmtm-items-center fmtm-justify-end xl:fmtm-w-fit fmtm-gap-3">
          {filter?.task_id &&
            projectData?.[projectIndex]?.taskBoundries?.find((task) => task?.id === +filter?.task_id)?.task_state ===
              task_state.LOCKED_FOR_VALIDATION && (
              <Button variant="primary-red" onClick={handleTaskMap} isLoading={updateTaskStatusLoading}>
                MARK AS VALIDATED
              </Button>
            )}
          {toggleView}
        </div>
      </div>
      {submissionTableDataLoading || submissionFormFieldsLoading ? (
        <SubmissionsTableSkeleton />
      ) : (
        <Table data={submissionTableData?.results || []} flag="dashboard" onRowClick={() => {}} isLoading={false}>
          <TableHeader
            dataField="SN"
            headerClassName="snHeader"
            rowClassName="snRow"
            dataFormat={(row, _, index) => <span>{index + 1}</span>}
          />
          <TableHeader
            dataField="Review State"
            headerClassName="codeHeader"
            rowClassName="codeRow"
            dataFormat={(row) => (
              <div className="fmtm-w-[7rem] fmtm-overflow-hidden fmtm-truncate">
                <span>{row?.__system?.reviewState ? camelToFlat(row?.__system?.reviewState) : 'Received'}</span>
              </div>
            )}
          />
          {updatedSubmissionFormFields?.map((field: any): React.ReactNode | null => {
            if (field) {
              return (
                <TableHeader
                  key={field?.path}
                  dataField={field?.name}
                  headerClassName="codeHeader"
                  rowClassName="codeRow"
                  dataFormat={(row) => {
                    const value = getValueByPath(row, field?.path);
                    return (
                      <Tooltip arrow placement="bottom-start" title={value}>
                        <div className="fmtm-w-[7rem] fmtm-overflow-hidden fmtm-truncate">
                          <span className="fmtm-text-[15px]">{value}</span>
                        </div>
                      </Tooltip>
                    );
                  }}
                />
              );
            }
            return null;
          })}
          <TableHeader
            dataField="Actions"
            headerClassName="updatedHeader !fmtm-sticky fmtm-right-0 fmtm-shadow-[-10px_0px_20px_0px_rgba(0,0,0,0.1)] fmtm-text-center"
            rowClassName="updatedRow !fmtm-sticky fmtm-right-0 fmtm-bg-white fmtm-shadow-[-10px_0px_20px_0px_rgba(0,0,0,0.1)]"
            dataFormat={(row) => {
              const taskUid = taskList?.find((task) => task?.index == row?.task_id)?.id;
              return (
                <div className="fmtm-w-[5rem] fmtm-overflow-hidden fmtm-truncate fmtm-text-center">
                  <Link to={`/project-submissions/${projectId}/tasks/${taskUid}/submission/${row?.meta?.instanceID}`}>
                    <Tooltip arrow placement="bottom" title="Validate Submission">
                      <AssetModules.VisibilityOutlinedIcon className="fmtm-text-[#545454] hover:fmtm-text-primaryRed" />
                    </Tooltip>
                  </Link>
                  {(isProjectManager || isOrganizationAdmin) && projectInfo.status === project_status.PUBLISHED && (
                    <>
                      <span className="fmtm-text-primaryRed fmtm-border-[1px] fmtm-border-primaryRed fmtm-mx-1"></span>{' '}
                      <Tooltip arrow placement="bottom" title="Update Review Status">
                        <AssetModules.CheckOutlinedIcon
                          className="fmtm-text-[#545454] hover:fmtm-text-primaryRed"
                          onClick={() => {
                            dispatch(
                              SubmissionActions.SetUpdateReviewStatusModal({
                                toggleModalStatus: true,
                                instanceId: row?.meta?.instanceID,
                                taskId: row?.task_id,
                                projectId: projectId,
                                reviewState: row?.__system?.reviewState,
                                entity_id: row?.feature,
                                label: row?.meta?.entity?.label,
                                taskUid: taskUid?.toString() || null,
                              }),
                            );
                          }}
                        />
                      </Tooltip>
                    </>
                  )}
                </div>
              );
            }}
          />
        </Table>
      )}
      {submissionTableData?.pagination && (
        <div
          style={{ fontFamily: 'BarlowMedium' }}
          className="fmtm-flex fmtm-items-center fmtm-justify-end fmtm-gap-2 sm:fmtm-gap-4"
        >
          <CoreModules.TablePagination
            component="div"
            count={submissionTableData?.pagination?.total}
            page={submissionTableData?.pagination?.page ? submissionTableData?.pagination?.page - 1 : 1}
            onPageChange={handleChangePage}
            rowsPerPage={submissionTableData?.pagination?.per_page}
            rowsPerPageOptions={[]}
            backIconButtonProps={{
              disabled:
                submissionTableDataLoading || submissionFormFieldsLoading || !submissionTableData?.pagination?.prev_num,
            }}
            nextIconButtonProps={{
              disabled:
                submissionTableDataLoading || submissionFormFieldsLoading || !submissionTableData?.pagination?.next_num,
            }}
            sx={{
              '&.MuiTablePagination-root': {
                display: 'flex',
                justifyContent: 'flex-end',
              },
              '& .MuiOutlinedInput-root': {
                '&.Mui-focused fieldset': {
                  borderColor: 'black',
                },
              },
              '&.Mui-focused .MuiFormLabel-root-MuiInputLabel-root': {
                color: 'black',
              },
              '.MuiTablePagination-spacer': { display: 'none' },
              '.MuiTablePagination-actions': {
                display: 'flex',
                '.MuiIconButton-root': { width: '30px', height: '30px' },
              },
            }}
            onRowsPerPageChange={() => {}}
          />
          <p className="fmtm-text-sm">Jump to</p>
          <input
            type="number"
            className={`fmtm-border-[1px] fmtm-border-[#E7E2E2] fmtm-text-sm fmtm-rounded-sm fmtm-w-11 fmtm-outline-none ${
              submissionTableDataLoading || (submissionFormFieldsLoading && 'fmtm-cursor-not-allowed')
            }`}
            onKeyDown={(e) => {
              if (e.currentTarget.value) {
                handleChangePage(e, parseInt(e.currentTarget.value) - 1);
              }
            }}
            disabled={submissionTableDataLoading || submissionFormFieldsLoading}
          />
        </div>
      )}
    </div>
  );
};

export default SubmissionsTable;
