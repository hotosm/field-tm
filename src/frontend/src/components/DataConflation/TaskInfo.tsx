import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Button from '@/components/common/Button';
import AssetModules from '@/shared/AssetModules';
import CoreModules from '@/shared/CoreModules';
import { useAppSelector } from '@/types/reduxTypes';

const TaskInfo = () => {
  const navigate = useNavigate();
  const { taskId, projectId } = useParams();

  const submissionConflationGeojson = useAppSelector((state) => state.dataconflation.submissionConflationGeojson);
  const submissionConflationGeojsonLoading = useAppSelector(
    (state) => state.dataconflation.submissionConflationGeojsonLoading,
  );
  const submissionFeatures = submissionConflationGeojson?.features;

  const featureCount = submissionFeatures?.length || 0;
  let geometryConflictCount = 0;
  let tagConflictCount = 0;
  let noTagConflictCount = 0;

  submissionFeatures?.map((feature) => {
    if (!feature) return;

    // geom conflict count
    if (feature?.properties?.overlap_percent < 90) {
      geometryConflictCount += 1;
    }

    if (!feature?.tags) return;
    let tagConflict = false;
    let noConflict = false;

    // tag conflict count
    for (const [key, value] of Object.entries(feature?.tags)) {
      if (feature?.properties?.[key] && feature?.properties?.[key] !== value) {
        tagConflict = true;
      } else if (feature?.properties?.overlap_percent > 90) {
        noConflict = true;
      }
    }
    if (tagConflict) tagConflictCount += 1;
    if (noConflict) noTagConflictCount += 1;
  });

  const taskInfoConstants = [
    { name: 'Total Feature', count: featureCount - geometryConflictCount },
    { name: 'Number of geometry conflicts', count: geometryConflictCount },
    { name: 'Number of tag conflicts', count: tagConflictCount },
    { name: 'No conflicts', count: noTagConflictCount },
  ];

  return (
    <div className="fmtm-h-full">
      <div
        onClick={() => navigate(`/project/${projectId}`)}
        className="fmtm-flex fmtm-items-center fmtm-mb-5 fmtm-cursor-pointer hover:fmtm-text-primaryRed fmtm-duration-300 fmtm-w-fit"
      >
        <AssetModules.ArrowBackIosIcon style={{ fontSize: '1.125rem' }} />
        <p className="fmtm-text-sm fmtm-font-[500]">BACK</p>
      </div>
      <div className="fmtm-w-full fmtm-py-3 lg:fmtm-py-2 fmtm-px-3 fmtm-bg-white lg:fmtm-h-[calc(100%-2.5rem)] fmtm-flex fmtm-flex-col sm:fmtm-flex-row lg:fmtm-flex-col fmtm-gap-x-10">
        <div>
          <p className="fmtm-text-primaryRed">Task #{taskId}</p>

          <div className="fmtm-mt-5 fmtm-mb-5 sm:fmtm-mb-0 lg:fmtm-mb-10">
            {submissionConflationGeojsonLoading ? (
              <>
                {Array.from({ length: 4 }).map((_, index) => (
                  <CoreModules.Skeleton key={index} className="!fmtm-w-[12.5rem] fmtm-h-[0.75rem]" />
                ))}
              </>
            ) : (
              <table>
                {taskInfoConstants?.map((info) => (
                  <tr className="">
                    <td className="fmtm-text-base fmtm-text-[#484848] fmtm-pb-1">{info?.name}</td>
                    <td className="fmtm-text-base fmtm-text-[#484848] fmtm-px-2 fmtm-pb-1">:</td>
                    <td className="fmtm-text-base fmtm-text-[#484848] fmtm-pb-1">{info?.count}</td>
                  </tr>
                ))}
              </table>
            )}
          </div>
        </div>

        <div className="fmtm-flex fmtm-flex-col fmtm-gap-3 fmtm-justify-end">
          <Button
            btnText="Submit Task"
            type="button"
            btnType="primary"
            onClick={() => {}}
            className="fmtm-text-sm !fmtm-rounded fmtm-w-full fmtm-justify-center"
            disabled={submissionConflationGeojsonLoading}
          />
          <Button
            btnText="Request Additional Mapping"
            type="button"
            btnType="other"
            onClick={() => {}}
            className="fmtm-text-sm !fmtm-rounded fmtm-w-full fmtm-justify-center"
            disabled={submissionConflationGeojsonLoading}
          />
        </div>
      </div>
    </div>
  );
};

export default TaskInfo;
