import React from 'react';
import CoreModules from '../../shared/CoreModules';

const ProjectInfoSidebarSkeleton = () => {
  return (
    <div>
      <div
        style={{
          borderBottom: '1px solid #EBEBEB',
          paddingTop: '10px',
          paddingBottom: '10px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <div style={{ width: '5%', maxWidth: '25px' }}>
            <CoreModules.Skeleton />
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              width: '85%',
              gap: '2%',
            }}
          >
            <div style={{ width: '60%', maxWidth: '170px' }}>
              <CoreModules.Skeleton />
            </div>
            <div style={{ width: '40%', maxWidth: '104px' }}>
              <CoreModules.Skeleton />
            </div>
          </div>
        </div>
        <div style={{ width: '30%', maxWidth: '140px' }}>
          <CoreModules.Skeleton count={2} />
        </div>
        <div style={{ paddingLeft: '60%' }}>
          <CoreModules.Skeleton />
        </div>
        <CoreModules.Skeleton />
      </div>
    </div>
  );
};

export default ProjectInfoSidebarSkeleton;
