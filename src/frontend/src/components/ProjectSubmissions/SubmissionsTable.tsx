import React, { useEffect, useState } from 'react';
import AssetModules from '@/shared/AssetModules.js';
import { CustomSelect } from '@/components/common/Select.js';
import windowDimention from '@/hooks/WindowDimension';
import Table, { TableHeader } from '@/components/common/CustomTable';
import { SubmissionFormFieldsService, SubmissionTableService } from '@/api/SubmissionService';
import CoreModules from '@/shared/CoreModules.js';
import environment from '@/environment';
import { SubmissionsTableSkeletonLoader } from '@/components/ProjectSubmissions/ProjectSubmissionsSkeletonLoader.js';
import { Loader2 } from 'lucide-react';
import { SubmissionActions } from '@/store/slices/SubmissionSlice';

type filterType = {
  taskId: number | null;
  submittedBy: string | null;
  reviewState: string | null;
  submittedDate: Date | null;
};

const SubmissionsTable = () => {
  const initialFilterState = {
    taskId: null,
    submittedBy: null,
    reviewState: null,
    submittedDate: null,
  };
  const [showFilter, setShowFilter] = useState<boolean>(true);
  const [filter, setFilter] = useState<filterType>(initialFilterState);
  const { windowSize } = windowDimention();
  const dispatch = CoreModules.useAppDispatch();
  const params = CoreModules.useParams();
  const encodedId = params.projectId;
  const decodedId = environment.decode(encodedId);
  const submissionFormFields = CoreModules.useAppSelector((state) => state.submission.submissionFormFields);
  const submissionTableData = CoreModules.useAppSelector((state) => state.submission.submissionTableData);
  const submissionFormFieldsLoading = CoreModules.useAppSelector(
    (state) => state.submission.submissionFormFieldsLoading,
  );
  const submissionTableDataLoading = CoreModules.useAppSelector((state) => state.submission.submissionTableDataLoading);
  const submissionTableRefreshing = CoreModules.useAppSelector((state) => state.submission.submissionTableRefreshing);
  const taskInfo = CoreModules.useAppSelector((state) => state.task.taskInfo);
  const [numberOfFilters, setNumberOfFilters] = useState<number>(0);
  const [paginationPage, setPaginationPage] = useState<number>(1);

  useEffect(() => {
    let count = 0;
    const filters = Object.keys(filter);
    filters?.map((fltr) => {
      if (filter[fltr]) {
        count = count + 1;
      }
    });
    setNumberOfFilters(count);
  }, [filter]);

  const updatedSubmissionFormFields = submissionFormFields?.map((formField) => {
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
      SubmissionFormFieldsService(`${import.meta.env.VITE_API_URL}/submission/submission_form_fields/${decodedId}`),
    );
  }, []);

  useEffect(() => {
    if (!filter.taskId) {
      dispatch(
        SubmissionTableService(
          `${import.meta.env.VITE_API_URL}/submission/submission_table/${decodedId}?page=${paginationPage}`,
        ),
      );
    } else {
      dispatch(
        SubmissionTableService(
          `${import.meta.env.VITE_API_URL}/submission/task_submissions/${decodedId}?task_id=${
            filter.taskId
          }&page=${paginationPage}`,
        ),
      );
    }
  }, [paginationPage]);

  useEffect(() => {
    setPaginationPage(1);
    if (!filter.taskId) {
      dispatch(
        SubmissionTableService(`${import.meta.env.VITE_API_URL}/submission/submission_table/${decodedId}?page=1`),
      );
    } else {
      dispatch(
        SubmissionTableService(
          `${import.meta.env.VITE_API_URL}/submission/task_submissions/${decodedId}?task_id=${filter.taskId}&page=1`,
        ),
      );
    }
  }, [filter]);

  const refreshTable = () => {
    dispatch(
      SubmissionFormFieldsService(`${import.meta.env.VITE_API_URL}/submission/submission_form_fields/${decodedId}`),
    );
    dispatch(SubmissionActions.SetSubmissionTableRefreshing(true));
    if (!filter.taskId) {
      dispatch(
        SubmissionTableService(
          `${import.meta.env.VITE_API_URL}/submission/submission_table/${decodedId}?page=${paginationPage}`,
        ),
      );
    } else {
      dispatch(
        SubmissionTableService(
          `${import.meta.env.VITE_API_URL}/submission/task_submissions/${decodedId}?task_id=${
            filter.taskId
          }&page=${paginationPage}`,
        ),
      );
    }
  };

  const handleChangePage = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | React.KeyboardEvent<HTMLInputElement>,
    newPage: number,
  ) => {
    if (newPage + 1 > submissionTableData?.pagination?.pages || newPage + 1 < 1) {
      setPaginationPage(paginationPage);
      return;
    }
    setPaginationPage(newPage + 1);
  };

  const clearFilters = () => {
    setFilter(initialFilterState);
  };

  const TableFilter = () => (
    <div className="fmtm-flex fmtm-items-center fmtm-justify-between fmtm-flex-col sm:fmtm-flex-row fmtm-gap-4">
      <div
        className={`fmtm-bg-white ${
          windowSize.width < 2000 ? 'fmtm-w-full md:fmtm-w-fit' : 'fmtm-w-fit'
        } fmtm-flex xl:fmtm-items-end fmtm-gap-2 xl:fmtm-gap-8 fmtm-px-4 fmtm-rounded-lg fmtm-relative fmtm-pr-6 fmtm-flex-col xl:fmtm-flex-row fmtm-py-2 fmtm-pt-3 xl:fmtm-py-2  fmtm-my-2`}
      >
        <div className="fmtm-flex fmtm-justify-between fmtm-items-center fmtm-gap-8">
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-mb-1 fmtm-relative fmtm-w-fit">
            <div>
              <AssetModules.FilterAltOutlinedIcon className="fmtm-text-grey-700" />
            </div>
            <p className="fmtm-text-sm fmtm-mt-1 fmtm-text-grey-700 fmtm-font-bold">FILTER</p>
            <div className="fmtm-absolute -fmtm-right-3 -fmtm-top-2 fmtm-w-4 fmtm-h-4 fmtm-rounded-full  fmtm-bg-primaryRed fmtm-flex fmtm-justify-center fmtm-items-center">
              <p className=" fmtm-text-xs fmtm-text-white">{numberOfFilters}</p>
            </div>
          </div>
          <button
            className={`fmtm-w-fit fmtm-text-sm fmtm-text-grey-700 fmtm-font-bold fmtm-duration-150 fmtm-truncate fmtm-block xl:fmtm-hidden ${
              !filter.taskId && !filter.reviewState && !filter.submittedBy && !filter.submittedDate
                ? 'fmtm-hidden'
                : 'fmtm-block'
            } ${
              submissionTableDataLoading || submissionFormFieldsLoading
                ? 'fmtm-cursor-not-allowed'
                : 'hover:fmtm-text-red-700'
            }`}
            onClick={clearFilters}
            disabled={submissionTableDataLoading || submissionFormFieldsLoading}
          >
            CLEAR ALL
          </button>
        </div>
        {showFilter && (
          <div
            className={`fmtm-grid ${
              windowSize.width < 500 ? 'fmtm-grid-cols-1' : 'fmtm-grid-cols-2 lg:fmtm-grid-cols-4'
            } fmtm-gap-4`}
          >
            <div className={`${windowSize.width < 500 ? 'fmtm-w-full' : 'fmtm-w-[11rem]'}`}>
              <CustomSelect
                title="Task Id"
                placeholder="Select"
                data={taskInfo}
                dataKey="value"
                value={filter?.taskId?.toString()}
                valueKey="task_id"
                label="task_id"
                onValueChange={(value) => value && setFilter((prev) => ({ ...prev, taskId: +value }))}
                className="fmtm-text-grey-700 fmtm-text-sm !fmtm-mb-0"
              />
            </div>
            <div className={`${windowSize.width < 500 ? 'fmtm-w-full' : 'fmtm-w-[11rem]'}`}>
              <CustomSelect
                title="Submitted By"
                placeholder="Select"
                data={[]}
                dataKey="value"
                value={''}
                valueKey="value"
                label="label"
                onValueChange={() => {}}
                errorMsg=""
                className="fmtm-text-grey-700 fmtm-text-sm !fmtm-mb-0"
              />
            </div>
            <div className={`${windowSize.width < 500 ? 'fmtm-w-full' : 'fmtm-w-[11rem]'}`}>
              <CustomSelect
                title="Review State"
                placeholder="Select"
                data={[]}
                dataKey="value"
                value={''}
                valueKey="value"
                label="label"
                onValueChange={() => {}}
                errorMsg=""
                className="fmtm-text-grey-700 fmtm-text-sm !fmtm-mb-0"
              />
            </div>
            <div className={`${windowSize.width < 500 ? 'fmtm-w-full' : 'fmtm-w-[11rem]'}`}>
              <CustomSelect
                title="Submitted Date"
                placeholder="Select"
                data={[]}
                dataKey="value"
                value={''}
                valueKey="value"
                label="label"
                onValueChange={() => {}}
                errorMsg=""
                className="fmtm-text-grey-700 fmtm-text-sm !fmtm-mb-0"
              />
            </div>
          </div>
        )}
        <button
          className={`fmtm-w-fit fmtm-text-sm fmtm-text-grey-700 fmtm-font-bold fmtm-mb-1  hover:fmtm-text-red-700 fmtm-duration-150 fmtm-truncate fmtm-hidden xl:fmtm-block`}
        >
          CLEAR ALL
        </button>
        <div
          className={`fmtm-group fmtm-absolute -fmtm-right-3 ${
            showFilter
              ? 'fmtm-top-[45%] sm:fmtm-top-20 lg:fmtm-top-9 xl:fmtm-top-5'
              : 'fmtm-top-2 xl:fmtm-top-1 fmtm-rotate-180'
          } fmtm-rounded-full  fmtm-w-7 fmtm-h-7 fmtm-bg-white fmtm-border-[1px] fmtm-border-gray-300 fmtm-flex fmtm-justify-center fmtm-items-center fmtm-pl-2 hover:fmtm-border-primaryRed fmtm-duration-150`}
          onClick={() => setShowFilter(!showFilter)}
        >
          <AssetModules.ArrowBackIosIcon
            className="fmtm-text-grey-700 group-hover:fmtm-text-primaryRed fmtm-duration-150"
            style={{ fontSize: '18px' }}
          />
        </div>
      </div>
      <div className="fmtm-w-full fmtm-flex fmtm-justify-end sm:fmtm-w-fit">
        <button
          className={`fmtm-px-4 fmtm-py-1 fmtm-flex fmtm-items-center fmtm-w-fit fmtm-rounded-lg fmtm-gap-2 fmtm-duration-150 ${
            submissionTableDataLoading || submissionFormFieldsLoading
              ? 'fmtm-bg-gray-400 fmtm-cursor-not-allowed'
              : 'fmtm-bg-primaryRed hover:fmtm-bg-red-700'
          }`}
          onClick={refreshTable}
          disabled={submissionTableDataLoading || submissionFormFieldsLoading}
        >
          {(submissionTableDataLoading || submissionFormFieldsLoading) && submissionTableRefreshing ? (
            <Loader2 className="fmtm-h-4 fmtm-w-4 fmtm-animate-spin fmtm-text-white" />
          ) : (
            <AssetModules.ReplayIcon className="fmtm-text-white" style={{ fontSize: '18px' }} />
          )}
          <p className="fmtm-text-white fmtm-pt-1">Refresh</p>
        </button>
      </div>
    </div>
  );

  function getValueByPath(obj: any, path: string) {
    let value = obj;
    path?.split('.')?.map((item) => {
      if (path === 'start' || path === 'end') {
        value = `${value[item]?.split('T')[0]} ${value[item]?.split('T')[1]}`;
      } else if (item === 'point') {
        value = `${value[item].type} (${value[item].coordinates})`;
      } else {
        value = value[item];
      }
    });
    return value ? value : '-';
  }

  return (
    <div className="fmtm-font-archivo">
      <TableFilter />
      {submissionTableDataLoading || submissionFormFieldsLoading ? (
        <SubmissionsTableSkeletonLoader />
      ) : (
        <Table data={submissionTableData?.results || []} flag="dashboard" onRowClick={() => {}} isLoading={false}>
          <TableHeader
            dataField="SN"
            headerClassName="snHeader"
            rowClassName="snRow"
            dataFormat={(row, _, index) => <span>{index + 1}</span>}
          />
          {updatedSubmissionFormFields?.map((field: any): React.ReactNode | null => {
            if (field) {
              return (
                <TableHeader
                  key={field?.path}
                  dataField={field?.name}
                  headerClassName="codeHeader"
                  rowClassName="codeRow"
                  dataFormat={(row) => (
                    <div
                      className="fmtm-w-[7rem] fmtm-overflow-hidden fmtm-truncate"
                      title={getValueByPath(row, field?.path)}
                    >
                      <span className="fmtm-text-[15px]">{getValueByPath(row, field?.path)}</span>
                    </div>
                  )}
                />
              );
            }
            return null;
          })}
          <TableHeader
            dataField="Actions"
            headerClassName="updatedHeader"
            rowClassName="updatedRow"
            dataFormat={(row) => (
              <div className="fmtm-w-[7rem] fmtm-overflow-hidden fmtm-truncate fmtm-text-center">
                <AssetModules.VisibilityOutlinedIcon className="fmtm-text-[#545454]" />{' '}
                <span className="fmtm-text-primaryRed fmtm-border-[1px] fmtm-border-primaryRed fmtm-mx-1"></span>{' '}
                <AssetModules.CheckOutlinedIcon className="fmtm-text-[#545454]" />{' '}
                <span className="fmtm-text-primaryRed fmtm-border-[1px] fmtm-border-primaryRed fmtm-mx-1"></span>{' '}
                <AssetModules.DeleteIcon className="fmtm-text-[#545454]" />
              </div>
            )}
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
            page={submissionTableData?.pagination?.page - 1}
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
