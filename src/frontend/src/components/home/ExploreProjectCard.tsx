import * as React from 'react';
import { useNavigate } from 'react-router-dom';
import { Tooltip } from '@mui/material';
import { projectType } from '@/models/home/homeModel';
import defaultOrgLogo from '@/assets/images/project_icon.png';

export default function ExploreProjectCard({ data, className }: { data: projectType; className?: string }) {
  const navigate = useNavigate();

  const handleProjectCardClick = () => {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    if (isMobile) {
      // Redirect to mapper frontend on mobile
      // (we hardcode mapper.xxx for now - open an issue if more flexibility is needed)
      const { protocol, hostname, port } = window.location;
      window.location.href = `${protocol}//mapper.${hostname}${port ? `:${port}` : ''}/${data.id}`;
    } else {
      // Else view project via manager frontend (desktop)
      navigate(`/project/${data.id}`);
    }
  };

  return (
    <div
      onClick={handleProjectCardClick}
      className={`hover:fmtm-bg-red-light hover:fmtm-shadow-xl fmtm-duration-500 fmtm-rounded-lg fmtm-border-solid fmtm-bg-white fmtm-p-4 fmtm-max-h-fit fmtm-cursor-pointer ${className}`}
    >
      <div className="fmtm-flex fmtm-flex-col fmtm-justify-between fmtm-h-full">
        <div>
          {data.organisation_logo ? (
            <img src={data.organisation_logo} className="fmtm-h-7 fmtm-max-h-7" alt="organization logo" />
          ) : (
            <img src={defaultOrgLogo} className="fmtm-h-7 fmtm-max-h-7" alt="default organization logo" />
          )}
          <div className="fmtm-my-3">
            <p className="fmtm-body-sm-semibold fmtm-text-[#706E6E] fmtm-mb-1">ID: #{data.id}</p>
            <p
              className="fmtm-capitalize fmtm-body-sm fmtm-line-clamp-1 fmtm-text-[#7A7676]"
              title={data?.location_str}
            >
              {data?.location_str || '-'}
            </p>
          </div>

          <div>
            <p
              className="fmtm-button fmtm-text-[#090909] fmtm-line-clamp-1 fmtm-capitalize fmtm-mb-1"
              title={data.name}
            >
              {data.name}
            </p>
            <p
              className="fmtm-body-md fmtm-capitalize fmtm-line-clamp-3 fmtm-text-[#2B2B2B] fmtm-min-h-[3.938rem]"
              title={data.short_description}
            >
              {data.short_description}
            </p>
          </div>
        </div>
        <div className="fmtm-mt-4">
          <div className="fmtm-flex fmtm-justify-between fmtm-mb-1">
            <p className="fmtm-body-sm-semibold">{data?.total_tasks} Tasks</p>
            <p className="fmtm-body-sm-semibold">{data?.total_submissions} Submissions</p>
          </div>
          <Tooltip
            title={
              <div>
                <p>{data?.total_tasks} Total Tasks</p>
                <p>{data?.tasks_mapped} Tasks Mapped</p>
                <p>{data?.tasks_validated} Tasks Validated</p>
              </div>
            }
            placement="top"
            arrow
            componentsProps={{
              tooltip: {
                sx: {
                  backgroundColor: '#333333',
                  color: '#ffffff',
                  fontSize: '12px',
                },
              },
              arrow: {
                sx: {
                  color: '#333333',
                },
              },
            }}
          >
            <div className="fmtm-h-[0.375rem] fmtm-w-full fmtm-bg-grey-300 fmtm-rounded-xl fmtm-overflow-hidden fmtm-flex fmtm-cursor-pointer">
              <div
                style={{
                  width: `${(data?.tasks_mapped / data?.total_tasks) * 100}%`,
                }}
                className={`fmtm-h-full fmtm-bg-grey-800 fmtm-rounded-r-xl`}
              />
              <div
                style={{
                  width: `${(data?.tasks_validated / data?.total_tasks) * 100}%`,
                }}
                className={`fmtm-h-full fmtm-bg-grey-500 fmtm-rounded-r-xl`}
              />
            </div>
          </Tooltip>
        </div>
      </div>
    </div>
  );
}
