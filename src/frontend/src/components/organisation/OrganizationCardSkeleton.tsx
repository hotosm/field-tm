import React from 'react';
import CoreModules from '@/shared/CoreModules';

const OrganisationCardSkeleton = ({ cardsPerRow, defaultTheme }) => {
  return cardsPerRow.map((data, index) => {
    return (
      <div
        key={`${data}-${index}`}
        style={{
          width: `${100 / cardsPerRow.length}%`,
          padding: 5,
          border: '1px solid lightgray',
          marginTop: '1%',
          marginLeft: '0.1%',
          marginRight: '0.1%',
          height: 'inherit',
        }}
      >
        <div className="fmtm-flex fmtm-gap-4">
          <div className="row fmtm-mt-3">
            <div className="col-md-12">
              <CoreModules.SkeletonTheme baseColor={defaultTheme.palette.loading['skeleton_rgb']}>
                <CoreModules.Skeleton width={100} style={{ marginTop: '3%' }} height={100} count={1} />
              </CoreModules.SkeletonTheme>
            </div>
          </div>

          <div className="row mt-2 fmtm-w-full">
            <div className="col-md-12">
              <CoreModules.SkeletonTheme baseColor={defaultTheme.palette.loading['skeleton_rgb']}>
                <CoreModules.Skeleton width={100} style={{ marginTop: '3%' }} count={1} />
              </CoreModules.SkeletonTheme>
            </div>
            <div className="col-md-4 mt-1">
              <CoreModules.SkeletonTheme
                baseColor={defaultTheme.palette.loading['skeleton_rgb']}
                highlightColor={defaultTheme.palette.loading['skeleton_rgb']}
              >
                <CoreModules.Skeleton height={20} count={2} />
              </CoreModules.SkeletonTheme>
            </div>
            <div className="col-md-12 fmtm-mt-4 fmtm-mb-2">
              <CoreModules.SkeletonTheme
                baseColor={defaultTheme.palette.loading['skeleton_rgb']}
                highlightColor={defaultTheme.palette.loading['skeleton_rgb']}
              >
                <CoreModules.Skeleton width={69} style={{ marginTop: '3%', float: 'right' }} count={1} />
              </CoreModules.SkeletonTheme>
            </div>
          </div>
        </div>
      </div>
    );
  });
};

export default OrganisationCardSkeleton;
