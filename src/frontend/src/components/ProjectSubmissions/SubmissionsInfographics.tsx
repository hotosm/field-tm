import React, { useEffect, useRef, useState } from 'react';
import TaskSubmissions from '@/components/ProjectSubmissions/TaskSubmissions';
import CustomBarChart from '@/components/common/BarChart';
import CustomPieChart from '@/components/common/PieChart';
import Table, { TableHeader } from '@/components/common/CustomTable';
import CustomLineChart from '@/components/common/LineChart';
import CoreModules from '@/shared/CoreModules';
import InfographicsCard from '@/components/ProjectSubmissions/InfographicsCard';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { useAppSelector } from '@/types/reduxTypes';
import { formSubmissionType } from '@/models/submission/submissionModel';
import { dateNDaysAgo, getMonthDate } from '@/utilfunctions/commonUtils';

const SubmissionsInfographics = ({ toggleView, entities }) => {
  useDocumentTitle('Submission Infographics');
  const formSubmissionRef = useRef(null);
  const projectProgressRef = useRef(null);
  const totalContributorsRef = useRef(null);
  const plannedVsActualRef = useRef(null);

  const submissionContributorsData = useAppSelector((state) => state.submission.submissionContributors);
  const submissionContributorsLoading = useAppSelector((state) => state.submission.submissionContributorsLoading);
  const [submissionProjection, setSubmissionProjection] = useState<10 | 30>(10);
  const taskInfo = useAppSelector((state) => state.task.taskInfo);
  const taskLoading = useAppSelector((state) => state.task.taskLoading);
  const entityOsmMapLoading = useAppSelector((state) => state.project.entityOsmMapLoading);
  const mappedVsValidatedTaskList = useAppSelector((state) => state.submission.mappedVsValidatedTask);
  const mappedVsValidatedTaskLoading = useAppSelector((state) => state.submission.mappedVsValidatedTaskLoading);

  const today = new Date().toISOString();
  const [formSubmissionsData, setFormSubmissionsData] = useState<formSubmissionType[]>([]);

  // data for validated vs mapped graph
  useEffect(() => {
    if (entities?.length === 0) return;

    // get entities updated within the last 10 or 30 days
    const updatedEntityLastNDays = entities?.filter((entity) => {
      const updatedDate = new Date(entity?.updated_at).toISOString();
      return updatedDate >= dateNDaysAgo(submissionProjection) && updatedDate <= today;
    });

    // group entity submission according to date
    const submissions: formSubmissionType[] = [];
    updatedEntityLastNDays?.map((entity) => {
      if (submissions?.find((submission) => submission.label === getMonthDate(entity.updated_at))) {
        const index = submissions.findIndex((submission) => submission.label === getMonthDate(entity.updated_at));
        submissions[index].count += entity?.submission_ids?.split(',')?.length;
      } else {
        submissions.push({
          date: entity.updated_at?.split('T')[0],
          label: getMonthDate(entity.updated_at),
          count: 1,
        });
      }
    });

    // sort submissions by ascending date
    const sortedEntitySubmissions = submissions?.sort((a, b) => {
      const date1: any = new Date(a.date);
      const date2: any = new Date(b.date);
      return date1 - date2;
    });
    setFormSubmissionsData(sortedEntitySubmissions);
  }, [entities, submissionProjection]);

  const FormSubmissionSubHeader = () => (
    <div className="fmtm-text-sm fmtm-flex fmtm-gap-5 fmtm-mb-2">
      <div
        className={`fmtm-border-b-[2px] fmtm-cursor-pointer  ${
          submissionProjection === 10 ? 'fmtm-border-[#f3c5c5]' : 'fmtm-border-white hover:fmtm-border-gray-300'
        }`}
        onClick={() => setSubmissionProjection(10)}
      >
        <p>Last 10 days</p>
      </div>
      <div
        className={`fmtm-border-b-[2px] fmtm-cursor-pointer ${
          submissionProjection === 30 ? 'fmtm-border-[#f3c5c5]' : 'fmtm-border-white hover:fmtm-border-gray-300'
        }`}
        onClick={() => setSubmissionProjection(30)}
      >
        <p>Last 30 days</p>
      </div>
    </div>
  );

  const totalFeatureCount = taskInfo.reduce((total, task) => total + task.feature_count, 0);
  const totalSubmissionCount = taskInfo.reduce((total, task) => total + task.submission_count, 0);
  const projectProgressData = [
    {
      names: 'Current',
      value:
        totalSubmissionCount > totalFeatureCount || (totalSubmissionCount === 0 && totalFeatureCount === 0)
          ? 100
          : totalSubmissionCount,
    },
    {
      names: 'Remaining',
      value: totalSubmissionCount > totalFeatureCount ? 0 : totalFeatureCount - totalSubmissionCount,
    },
  ];

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-5">
      {toggleView}
      <div className="fmtm-flex fmtm-flex-col lg:fmtm-flex-row fmtm-gap-5 lg:fmtm-gap-10">
        <div className="lg:fmtm-w-[60%] xl:fmtm-w-[70%]">
          <InfographicsCard
            cardRef={formSubmissionRef}
            header="Form Submissions"
            subHeader={<FormSubmissionSubHeader />}
            body={
              entityOsmMapLoading ? (
                <CoreModules.Skeleton className="!fmtm-w-full fmtm-h-full" />
              ) : formSubmissionsData.length > 0 ? (
                <CustomBarChart
                  data={formSubmissionsData}
                  xLabel="Submission Data"
                  yLabel="Submission Count"
                  dataKey="count"
                  nameKey="label"
                />
              ) : (
                <div className="fmtm-w-full fmtm-h-full fmtm-flex fmtm-justify-center fmtm-items-center fmtm-text-3xl fmtm-text-gray-400">
                  No form submissions!
                </div>
              )
            }
          />
        </div>
        <div className="lg:fmtm-w-[40%] xl:fmtm-w-[30%]">
          <InfographicsCard
            cardRef={projectProgressRef}
            header="Project Progress"
            body={
              taskLoading ? (
                <CoreModules.Skeleton className="!fmtm-w-full fmtm-h-full" />
              ) : (
                <CustomPieChart data={projectProgressData} dataKey="value" nameKey="names" />
              )
            }
          />
        </div>
      </div>
      <div className="fmtm-flex fmtm-flex-col lg:fmtm-flex-row fmtm-gap-5 lg:fmtm-gap-10">
        <div className="lg:fmtm-w-[60%] xl:fmtm-w-[70%]">
          <InfographicsCard
            cardRef={plannedVsActualRef}
            header="Validated vs Mapped Task"
            body={
              mappedVsValidatedTaskLoading ? (
                <CoreModules.Skeleton className="!fmtm-w-full fmtm-h-full" />
              ) : mappedVsValidatedTaskList.length > 0 ? (
                <CustomLineChart
                  data={mappedVsValidatedTaskList}
                  xAxisDataKey="label"
                  lineOneKey="validated"
                  lineTwoKey="mapped"
                  xLabel="Submission Date"
                  yLabel="Task Count"
                />
              ) : (
                <div className="fmtm-w-full fmtm-h-full fmtm-flex fmtm-justify-center fmtm-items-center fmtm-text-3xl fmtm-text-gray-400">
                  No Tasks Validated or Mapped in the Last 30 Days
                </div>
              )
            }
          />
        </div>
        <div className="lg:fmtm-w-[40%] xl:fmtm-w-[30%]">
          <InfographicsCard
            cardRef={totalContributorsRef}
            header={`Total Contributors: ${submissionContributorsData.length}`}
            body={
              <Table
                data={submissionContributorsData}
                onRowClick={() => {}}
                style={{ height: '100%' }}
                isLoading={submissionContributorsLoading}
              >
                <TableHeader
                  dataField="SN"
                  headerClassName="snHeader"
                  rowClassName="snRow"
                  dataFormat={(row, _, index) => <span>{index + 1}</span>}
                />

                <TableHeader
                  dataField="OSMID"
                  headerClassName="codeHeader"
                  rowClassName="codeRow"
                  dataFormat={(row) => (
                    <div
                      className="fmtm-w-[7rem] fmtm-max-w-[7rem]fmtm-overflow-hidden fmtm-truncate"
                      title={row?.user}
                    >
                      <span className="fmtm-text-[15px]">{row?.user}</span>
                    </div>
                  )}
                />
                <TableHeader
                  dataField="Submissions"
                  headerClassName="codeHeader"
                  rowClassName="codeRow"
                  dataFormat={(row) => (
                    <div
                      className="fmtm-w-[7rem] fmtm-max-w-[7rem] fmtm-overflow-hidden fmtm-truncate"
                      title={row?.submissions}
                    >
                      <span className="fmtm-text-[15px]">{row?.submissions}</span>
                    </div>
                  )}
                />
              </Table>
            }
          />
        </div>
      </div>
      {/* <div>
        <InfographicsCard
          cardRef={plannedVsActualRef}
          header="Planned vs Actual"
          body={
            false ? (
              <CoreModules.Skeleton className="!fmtm-w-full fmtm-h-full" />
            ) : lineKeyData.length > 0 ? (
              <CustomLineChart
                data={lineKeyData}
                xAxisDataKey="name"
                lineOneKey="Planned"
                lineTwoKey="Actual"
                xLabel="Submission Date"
                yLabel="Submission Count"
              />
            ) : (
              <div className="fmtm-w-full fmtm-h-full fmtm-flex fmtm-justify-center fmtm-items-center fmtm-text-3xl fmtm-text-gray-400">
                No data available!
              </div>
            )
          }
        />
      </div> */}
      <div>
        <TaskSubmissions />
      </div>
    </div>
  );
};

export default SubmissionsInfographics;
