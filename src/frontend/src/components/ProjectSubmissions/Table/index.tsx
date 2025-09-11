import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import { Tooltip } from '@mui/material';
import AssetModules from '@/shared/AssetModules.js';
import CoreModules from '@/shared/CoreModules.js';
import { Modal } from '@/components/common/Modal';
import Table, { TableHeader } from '@/components/common/CustomTable';
import UpdateReviewStatusModal from '@/components/ProjectSubmissions/Table/UpdateReviewStatusModal';
import Filter from '@/components/ProjectSubmissions/Table/Filter';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { project_status } from '@/types/enums';
import { filterType } from '@/store/types/ISubmissions';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';
import { SubmissionFormFieldsService, SubmissionTableService } from '@/api/SubmissionService';
import { camelToFlat } from '@/utilfunctions/commonUtils';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import SubmissionsTableSkeleton from '@/components/Skeletons/ProjectSubmissions.tsx/SubmissionsTableSkeleton';
import { useIsOrganizationAdmin, useIsProjectManager } from '@/hooks/usePermissions';

const VITE_API_URL = import.meta.env.VITE_API_URL;
type tempFilterType = Omit<filterType, 'submitted_date_range'> & {
  submitted_date_range: { start: Date | null; end: Date | null };
  page: number;
};

const SubmissionsTable = ({ toggleView }) => {
  useDocumentTitle('Submission Table');
  const [searchParams, setSearchParams] = useSearchParams();

  const getInitialFilterState = () => {
    const task_id = searchParams.get('task_id');
    const submitted_date_range = searchParams.get('submitted_date_range');
    const submitted_by = searchParams.get('submitted_by');
    const review_state = searchParams.get('review_state');
    const page = searchParams.get('page');

    let submittedDateRange: { start: Date | null; end: Date | null } = {
      start: null,
      end: null,
    };
    if (submitted_date_range) {
      submittedDateRange = {
        start: new Date(submitted_date_range?.split(',')?.[0]) || null,
        end: new Date(submitted_date_range?.split(',')?.[1]) || null,
      };
    } else {
      submittedDateRange = {
        start: null,
        end: null,
      };
    }
    const initialFilterState: tempFilterType = {
      task_id: task_id ? task_id : null,
      submitted_by: submitted_by ? submitted_by : null,
      review_state: review_state ? review_state : null,
      submitted_date_range: submittedDateRange,
      page: page ? +page : 1,
    };
    return initialFilterState;
  };

  const [tempFilter, setTempFilter] = useState<tempFilterType>(getInitialFilterState());
  const [filter, setFilter] = useState<filterType>({
    ...tempFilter,
    submitted_date_range:
      tempFilter?.submitted_date_range?.start && tempFilter?.submitted_date_range?.end
        ? `${format(new Date(tempFilter.submitted_date_range?.start as Date), 'yyyy-MM-dd')},${format(new Date(tempFilter.submitted_date_range?.end as Date), 'yyyy-MM-dd')}`
        : null,
  });
  console.log(tempFilter, '----> tempFilter');

  const dispatch = useAppDispatch();
  const params = CoreModules.useParams();

  const projectId = params.projectId;
  const submissionFormFields = useAppSelector((state) => state.submission.submissionFormFields);
  const submissionTableData = useAppSelector((state) => state.submission.submissionTableData);
  const submissionFormFieldsLoading = useAppSelector((state) => state.submission.submissionFormFieldsLoading);
  const submissionTableDataLoading = useAppSelector((state) => state.submission.submissionTableDataLoading);
  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const josmEditorError = useAppSelector((state) => state.task.josmEditorError);

  const projectData = useAppSelector((state) => state.project.projectTaskBoundries);
  const projectIndex = projectData.findIndex((project) => project.id == +projectId);
  const taskList = projectData[projectIndex]?.taskBoundries;

  const isProjectManager = useIsProjectManager(projectId as string);
  const isOrganizationAdmin = useIsOrganizationAdmin(projectInfo.organisation_id ? +projectInfo.organisation_id : null);

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
        ...filter,
      }),
    );
  }, [filter]);

  const refreshTable = () => {
    dispatch(SubmissionFormFieldsService(`${VITE_API_URL}/submission/submission-form-fields?project_id=${projectId}`));
    dispatch(SubmissionActions.SetSubmissionTableRefreshing(true));
    dispatch(
      SubmissionTableService(`${VITE_API_URL}/submission/submission-table?project_id=${projectId}`, {
        ...filter,
        page: 1,
      }),
    );
  };

  const handleChangePage = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | React.KeyboardEvent<HTMLInputElement>,
    newPage: number,
  ) => {
    if (!submissionTableData?.pagination?.pages) return;
    if (newPage + 1 > submissionTableData?.pagination?.pages || newPage + 1 < 1) {
      return;
    }
    setFilter({ ...filter, page: newPage + 1 });
  };
  console.log(tempFilter, 'tempFilter');

  const applyFilter = () => {
    const submitted_date_range =
      tempFilter.submitted_date_range.start && tempFilter.submitted_date_range.end
        ? `${format(new Date(tempFilter.submitted_date_range.start as Date), 'yyyy-MM-dd')},${format(new Date(tempFilter.submitted_date_range.end as Date), 'yyyy-MM-dd')}`
        : null;
    setFilter({
      ...tempFilter,
      page: 1,
      submitted_date_range: submitted_date_range,
    });

    let searchParams: Record<string, string> = { tab: 'table' };
    if (tempFilter.task_id) searchParams.task_id = tempFilter.task_id;
    if (tempFilter.review_state) searchParams.review_state = tempFilter.review_state;
    if (tempFilter.submitted_by) searchParams.submitted_by = tempFilter.submitted_by;
    if (submitted_date_range) searchParams.submitted_date_range = submitted_date_range;
    if (tempFilter.task_id) searchParams.task_id = tempFilter.task_id;

    setSearchParams(searchParams);
  };

  const clearFilters = () => {
    setSearchParams({ tab: 'table' });
    setTempFilter({
      task_id: null,
      submitted_by: null,
      review_state: null,
      submitted_date_range: {
        start: null,
        end: null,
      },
      page: 1,
    });
    setFilter({
      task_id: null,
      submitted_by: null,
      review_state: null,
      submitted_date_range: null,
      page: 1,
    });
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
      <Filter
        toggleView={toggleView}
        tempFilter={tempFilter}
        setTempFilter={setTempFilter}
        filter={filter}
        applyFilter={applyFilter}
        clearFilters={clearFilters}
        refreshTable={refreshTable}
      />
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
                  <Link to={`/project-submissions/${projectId}/tasks/${taskUid}/submission/${row?.__id}`}>
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
