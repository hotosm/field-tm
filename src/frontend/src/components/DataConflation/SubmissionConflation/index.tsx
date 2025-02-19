import React, { useState } from 'react';
import Button from '@/components/common/Button';
import AssetModules from '@/shared/AssetModules';
import MergeAttributes from '@/components/DataConflation/SubmissionConflation/MergeAttributes';
import CoreModules from '@/shared/CoreModules';
import { useAppSelector } from '@/types/reduxTypes';

const TagsSkeleton = () => (
  <>
    {Array.from({ length: 6 }).map((_, index) => (
      <div className="fmtm-grid fmtm-grid-cols-2 fmtm-border-b fmtm-border-[#E2E2E2] fmtm-py-1">
        <CoreModules.Skeleton key={index} className="!fmtm-w-[8rem] fmtm-h-[0.75rem]" />
        <CoreModules.Skeleton key={index} className="!fmtm-w-[5rem] fmtm-h-[0.75rem]" />
      </div>
    ))}
  </>
);

const RenderTags = ({ tag }: { tag: [string, any] }) => (
  <div className="fmtm-grid fmtm-grid-cols-2 fmtm-border-b fmtm-border-[#E2E2E2] fmtm-py-1">
    <p className="fmtm-text-sm fmtm-text-[#555] fmtm-font-bold">{tag?.[0]}</p>
    <p className="fmtm-text-sm fmtm-text-[#555]">{tag?.[1]}</p>
  </div>
);

const SubmissionConflation = () => {
  const [selectedConflateMethod, setSelectedConflateMethod] = useState<
    'submission_feature' | 'osm_feature' | 'merge_attributes' | ''
  >('');

  const submissionConflationGeojson = useAppSelector((state) => state.dataconflation.submissionConflationGeojson);
  const selectedFeatureOSMId = useAppSelector((state) => state.dataconflation.selectedFeatureOSMId);
  const submissionConflationGeojsonLoading = useAppSelector(
    (state) => state.dataconflation.submissionConflationGeojsonLoading,
  );

  const selectedFeature = submissionConflationGeojson?.features?.find(
    (feature) => feature.properties?.xid === selectedFeatureOSMId,
  );
  const filteredSubmissionTags = {};
  for (const [key, value] of Object.entries(selectedFeature?.properties)) {
    if (value !== null) {
      filteredSubmissionTags[key] = value;
    }
  }

  return (
    <>
      <MergeAttributes
        selectedConflateMethod={selectedConflateMethod}
        setSelectedConflateMethod={setSelectedConflateMethod}
        submissionTags={filteredSubmissionTags}
        osmTags={selectedFeature?.tags}
      />
      <div className="fmtm-w-full fmtm-h-full">
        <div className="fmtm-flex fmtm-flex-col fmtm-gap-5 fmtm-h-full fmtm-relative">
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-2 fmtm-max-h-[40vh] md:fmtm-max-h-[40%]">
            <h4>SUBMISSION #457</h4>
            <div className="fmtm-bg-white fmtm-rounded-xl fmtm-p-3 fmtm-h-[calc(100%-4.281rem)] fmtm-overflow-y-scroll scrollbar">
              {submissionConflationGeojsonLoading ? (
                <TagsSkeleton />
              ) : filteredSubmissionTags ? (
                <>
                  {Object.entries(filteredSubmissionTags).map((tag) => {
                    const [key, value] = tag;
                    if (value) return <RenderTags tag={tag} />;
                  })}
                </>
              ) : (
                <></>
              )}
            </div>
            {/* TODO: update & fix button on feature development */}
            {/* <Button
              btnText="Accept Submission Feature"
              btnType="other"
              type="button"
              className={`${
                selectedConflateMethod === 'submission_feature'
                  ? 'fmtm-bg-[#40AC8C] fmtm-text-white hover:fmtm-text-white'
                  : ''
              } fmtm-py-2 fmtm-px-4 fmtm-text-sm fmtm-mx-auto fmtm-border-none !fmtm-rounded`}
              icon={
                selectedConflateMethod !== 'submission_feature' && (
                  <AssetModules.DoneIcon style={{ fontSize: '16px' }} />
                )
              }
              onClick={() => setSelectedConflateMethod('submission_feature')}
            /> */}
          </div>

          <div className="fmtm-flex fmtm-flex-col fmtm-gap-2 fmtm-max-h-[40vh] md:fmtm-max-h-[40%]">
            <h4>OSM TAGS</h4>
            <div className="fmtm-bg-white fmtm-rounded-xl fmtm-p-3 fmtm-h-[calc(100%-4.281rem)] fmtm-overflow-y-scroll scrollbar">
              {submissionConflationGeojsonLoading ? (
                <TagsSkeleton />
              ) : selectedFeature?.tags ? (
                <>
                  {Object.entries(selectedFeature?.tags).map((tag) => (
                    <RenderTags tag={tag} />
                  ))}
                </>
              ) : (
                <></>
              )}
            </div>
            {/* TODO: update & fix button on feature development */}
            {/* <Button
              btnText="Accept OSM Features"
              btnType="other"
              type="button"
              className={`${
                selectedConflateMethod === 'osm_feature'
                  ? 'fmtm-bg-[#40AC8C] fmtm-text-white hover:fmtm-text-white'
                  : ''
              } fmtm-py-2 fmtm-px-4 fmtm-text-sm fmtm-mx-auto fmtm-border-none !fmtm-rounded`}
              icon={selectedConflateMethod !== 'osm_feature' && <AssetModules.DoneIcon style={{ fontSize: '16px' }} />}
              onClick={() => setSelectedConflateMethod('osm_feature')}
            /> */}
          </div>

          <div className="md:fmtm-absolute md:fmtm-bottom-0 fmtm-w-full">
            {/* TODO: update & fix button on feature development */}
            {/* <Button
              btnText="Merge Attributes"
              btnType="other"
              type="button"
              className={`${
                selectedConflateMethod === 'merge_attributes'
                  ? 'fmtm-bg-[#40AC8C] fmtm-text-white hover:fmtm-text-white !fmtm-border-[#40AC8C] hover:fmtm-border-[#40AC8C]'
                  : ''
              } fmtm-py-2 fmtm-px-4 fmtm-text-sm fmtm-w-full fmtm-justify-center !fmtm-rounded`}
              onClick={() => setSelectedConflateMethod('merge_attributes')}
            /> */}
          </div>
        </div>
      </div>
    </>
  );
};

export default SubmissionConflation;
