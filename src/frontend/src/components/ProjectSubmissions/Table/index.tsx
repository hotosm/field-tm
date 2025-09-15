import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import { Tooltip } from '@mui/material';
import AssetModules from '@/shared/AssetModules.js';
import CoreModules from '@/shared/CoreModules.js';
import { Modal } from '@/components/common/Modal';
import UpdateReviewStatusModal from '@/components/ProjectSubmissions/Table/UpdateReviewStatusModal';
import Filter from '@/components/ProjectSubmissions/Table/Filter';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { project_status } from '@/types/enums';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { useIsOrganizationAdmin, useIsProjectManager } from '@/hooks/usePermissions';
import DataTable from '@/components/common/DataTable';
import { useGetSubmissionFormFieldsQuery, useGetSubmissionTableQuery } from '@/api/submission';

interface baseFilterType<T> {
  task_id: string | undefined;
  submitted_by: string | undefined;
  review_state: string | undefined;
  submitted_date_range: T;
  pageIndex: number;
  pageSize: number;
}

type tempFilterType = baseFilterType<{ start: Date | null; end: Date | null }>;
type filterType = baseFilterType<string | undefined>;

const SubmissionsTable = ({ toggleView }) => {
  useDocumentTitle('Submission Table');
  const [searchParams, setSearchParams] = useSearchParams();

  const getInitialFilterState = () => {
    const task_id = searchParams.get('task_id');
    const submitted_date_range = searchParams.get('submitted_date_range');
    const submitted_by = searchParams.get('submitted_by');
    const review_state = searchParams.get('review_state');

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
    const initialFilterState = {
      task_id: task_id ? task_id : undefined,
      submitted_by: submitted_by ? submitted_by : undefined,
      review_state: review_state ? review_state : undefined,
      submitted_date_range: submittedDateRange,
    };
    return { ...initialFilterState, pageIndex: 0, pageSize: 13 };
  };

  const [tempFilter, setTempFilter] = useState<tempFilterType>(getInitialFilterState());
  const [filter, setFilter] = useState<filterType>({
    ...tempFilter,
    submitted_date_range:
      tempFilter?.submitted_date_range?.start && tempFilter?.submitted_date_range?.end
        ? `${format(new Date(tempFilter.submitted_date_range?.start as Date), 'yyyy-MM-dd')},${format(new Date(tempFilter.submitted_date_range?.end as Date), 'yyyy-MM-dd')}`
        : undefined,
  });

  const dispatch = useAppDispatch();
  const params = CoreModules.useParams();

  const projectId = params.projectId;
  const projectInfo = useAppSelector((state) => state.project.projectInfo);
  const josmEditorError = useAppSelector((state) => state.task.josmEditorError);

  const projectData = useAppSelector((state) => state.project.projectTaskBoundries);
  const projectIndex = projectData.findIndex((project) => project.id == +projectId);
  const taskList = projectData[projectIndex]?.taskBoundries;

  const isProjectManager = useIsProjectManager(projectId as string);
  const isOrganizationAdmin = useIsOrganizationAdmin(projectInfo.organisation_id ? +projectInfo.organisation_id : null);

  const { data: submissionFormFields, isLoading: isSubmissionFormFieldsLoading } = useGetSubmissionFormFieldsQuery({
    params: { project_id: projectId },
    options: { queryKey: ['submission-form-fields', +projectId], staleTime: 60 * 60 * 1000 },
  });

  const {
    data: submissionTableData,
    isLoading: isSubmissionTableDataLoading,
    refetch: refreshTable,
  } = useGetSubmissionTableQuery({
    params: {
      project_id: projectId,
      review_state: filter.review_state,
      task_id: filter.task_id ? +filter.task_id : undefined,
      submitted_by: filter.submitted_by,
      submitted_date_range: filter.submitted_date_range,
      page: filter.pageIndex + 1,
      results_per_page: filter.pageSize,
    },
    options: { queryKey: ['submission-table-data', filter], staleTime: 60 * 1000 },
  });

  const updatedSubmissionFormFields =
    submissionFormFields
      //filter necessary fields only
      ?.filter(
        (formField) =>
          (formField?.path.startsWith('/survey_questions') ||
            ['/start', '/end', '/username', '/task_id', '/status'].includes(formField?.path)) &&
          formField.type !== 'structure',
      )
      // convert path to dot notation & update name
      ?.map((formField) => {
        return {
          ...formField,
          path: formField?.path.slice(1).replace(/\//g, '.'),
          name: formField?.name.charAt(0).toUpperCase() + formField?.name.slice(1).replace(/_/g, ' '),
        };
      }) || [];

  const applyFilter = () => {
    const submitted_date_range =
      tempFilter.submitted_date_range.start && tempFilter.submitted_date_range.end
        ? `${format(new Date(tempFilter.submitted_date_range.start as Date), 'yyyy-MM-dd')},${format(new Date(tempFilter.submitted_date_range.end as Date), 'yyyy-MM-dd')}`
        : undefined;
    setTempFilter({ ...tempFilter, pageIndex: 0 });
    setFilter({
      ...tempFilter,
      pageIndex: 0,
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
      task_id: undefined,
      submitted_by: undefined,
      review_state: undefined,
      submitted_date_range: {
        start: null,
        end: null,
      },
      pageIndex: 0,
      pageSize: 13,
    });
    setFilter({
      task_id: undefined,
      submitted_by: undefined,
      review_state: undefined,
      submitted_date_range: undefined,
      pageIndex: 0,
      pageSize: 13,
    });
  };

  const submissionDataColumns = [
    {
      header: 'S.N',
      cell: ({ cell }: { cell: any }) => cell.row.index + 1,
    },
    {
      header: 'Review State',
      accessorKey: '__system.reviewState',
      accessorFn: (row: any) => {
        return row.__system;
      },
      cell: ({ renderValue }) => {
        const val = renderValue();
        return <p className="fmtm-capitalize">{val.reviewState || 'Received'}</p>;
      },
    },
    ...updatedSubmissionFormFields?.map((field) => ({
      header: field?.name,
      accessorKey: field?.path,
      cell: ({ getValue }) => {
        return <p className="fmtm-capitalize">{getValue()}</p>;
      },
    })),
    {
      header: 'Actions',
      cell: ({ row }: any) => {
        const currRow = row?.original;
        const taskUid = taskList?.find((task) => task?.index == currRow?.task_id)?.id;
        return (
          <div className="fmtm-w-[5rem] fmtm-overflow-hidden fmtm-truncate fmtm-text-center">
            <Link to={`/project-submissions/${projectId}/tasks/${taskUid}/submission/${currRow?.__id}`}>
              <Tooltip arrow placement="bottom" title="Validate Submission">
                <AssetModules.VisibilityOutlinedIcon className="fmtm-text-[#545454] hover:fmtm-text-primaryRed" />
              </Tooltip>
            </Link>
            {(isProjectManager || isOrganizationAdmin) && projectInfo.status === project_status.PUBLISHED && (
              <>
                <span className="fmtm-text-primaryRed fmtm-border-[1px] fmtm-border-primaryRed fmtm-mx-1"></span>{' '}
                <Tooltip arrow placement="bottom" title="Update Review Status">
                  <AssetModules.CheckOutlinedIcon
                    className="fmtm-text-[#545454] hover:fmtm-text-primaryRed fmtm-cursor-pointer"
                    onClick={() => {
                      dispatch(
                        SubmissionActions.SetUpdateReviewStatusModal({
                          toggleModalStatus: true,
                          instanceId: currRow?.meta?.instanceID,
                          taskId: currRow?.task_id,
                          projectId: projectId,
                          reviewState: currRow?.__system?.reviewState,
                          entity_id: currRow?.feature,
                          label: currRow?.meta?.entity?.label,
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
      },
    },
  ];

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
      <DataTable
        data={submissionTableData || []}
        columns={submissionDataColumns}
        isLoading={isSubmissionTableDataLoading || isSubmissionFormFieldsLoading}
        pagination={{ pageIndex: tempFilter.pageIndex, pageSize: tempFilter.pageSize }}
        setPaginationPage={(page) => {
          setTempFilter(page);
          setFilter(page);
        }}
        tableWrapperClassName="fmtm-flex-1"
        initialState={{
          columnPinning: {
            right: ['Actions'],
          },
        }}
      />
    </div>
  );
};

export default SubmissionsTable;
