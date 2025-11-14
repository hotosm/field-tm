import { useGetMetricsQuery } from '@/api/helper';
import React from 'react';
import { Skeleton } from '@/components/Skeletons';
import { MotionCounter } from '../common/MotionCounter';

const Metric = () => {
  const { data: metrics, isLoading: isMetricsLoading } = useGetMetricsQuery({
    options: { queryKey: ['get-metrics'], staleTime: 60 * 60 * 1000 },
  });

  const metricData = [
    { count: metrics?.total_features_surveyed || 0, label: 'Features Surveyed', hasMore: true },
    { count: metrics?.total_projects || 0, label: 'Projects Created', hasMore: false },
    { count: metrics?.countries_covered || 0, label: 'Countries Covered', hasMore: false },
    { count: metrics?.total_users || 0, label: 'Users Registered', hasMore: false },
    { count: metrics?.total_organisations || 0, label: 'Organisations Registered', hasMore: false },
  ];

  return (
    <div className="fmtm-flex fmtm-w-full fmtm-px-[2rem] sm:fmtm-px-[3rem] md:fmtm-px-[4.5rem] fmtm-justify-around fmtm-flex-wrap fmtm-gap-x-5 fmtm-gap-y-2">
      {metricData.map((metric) => (
        <div key={metric.label} className="fmtm-flex fmtm-flex-col fmtm-items-center">
          <h1 className="fmtm-text-red-medium">
            {isMetricsLoading ? (
              <Skeleton className="fmtm-w-[4.5rem] fmtm-h-[4.5rem] fmtm-mb-5 !fmtm-rounded-full" />
            ) : (
              <MotionCounter from={0} to={metric.count} hasMore={metric.hasMore} />
            )}
          </h1>
          <p className="fmtm-body-lg-semibold fmtm-text-nowrap fmtm-text-blue-dark">{metric.label}</p>
        </div>
      ))}
    </div>
  );
};

export default Metric;
