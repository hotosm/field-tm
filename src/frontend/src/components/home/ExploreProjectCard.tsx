import * as React from 'react';
import { useNavigate } from 'react-router-dom';
import { Tooltip } from '@mui/material';
import AssetModules from '@/shared/AssetModules';
import StatusChip from '@/components/common/StatusChip';
import { field_mapping_app, project_status } from '@/types/enums';
import type { projectSummaryType } from '@/types';
import defaultOrgLogo from '@/assets/images/project_icon.png';
import QfieldLogo from '@/assets/images/qfield-logo.svg';
import ODKLogo from '@/assets/images/odk-logo.svg';
import HotLogo from '@/assets/images/favicon.svg';

const projectStatusVariantMap: Record<project_status, 'default' | 'info' | 'success' | 'error'> = {
  [project_status.DRAFT]: 'default',
  [project_status.PUBLISHED]: 'info',
  [project_status.COMPLETED]: 'success',
  [project_status.ARCHIVED]: 'error',
};

const fieldMappingAppLogoMap: Record<field_mapping_app, string> = {
  [field_mapping_app.FieldTM]: HotLogo,
  [field_mapping_app.ODK]: ODKLogo,
  [field_mapping_app.QField]: QfieldLogo,
};

export default function ExploreProjectCard({ data, className }: { data: projectSummaryType; className?: string }) {
  const navigate = useNavigate();

  const handleProjectCardClick = () => {
    // Else view project via manager frontend (desktop)
    if (data.status === project_status.DRAFT) {
      navigate(`/create-project/${data.id}?step=1`);
    } else {
      navigate(`/project/${data.id}`);
    }
  };

  return (
    <div
      onClick={handleProjectCardClick}
      className={`fmtm-relative hover:fmtm-bg-red-light hover:fmtm-shadow-xl fmtm-duration-500 fmtm-rounded-lg fmtm-border-solid fmtm-bg-white fmtm-p-4 fmtm-h-full fmtm-cursor-pointer ${className}`}
    >
      <div className="fmtm-flex fmtm-flex-col fmtm-justify-between fmtm-h-full">
        <div>
          <div className="fmtm-flex fmtm-justify-between fmtm-items-start">
            {data.organisation_logo ? (
              <img src={data.organisation_logo} className="fmtm-h-7 fmtm-max-h-7" alt="organization logo" />
            ) : (
              <img src={defaultOrgLogo} className="fmtm-h-7 fmtm-max-h-7" alt="default organization logo" />
            )}

            <div className="fmtm-flex fmtm-items-center fmtm-gap-2">
              {data.project_url && data.status !== project_status.DRAFT && (
                <Tooltip title={`Project created using ${data.field_mapping_app}`} arrow>
                  <img
                    src={fieldMappingAppLogoMap[data.field_mapping_app]}
                    className="fmtm-h-5 fmtm-max-h-5"
                    alt="qfield logo"
                  />
                </Tooltip>
              )}
              {[project_status.DRAFT, project_status.COMPLETED].includes(data.status) && (
                <StatusChip label={data.status.toLowerCase()} status={projectStatusVariantMap[data.status]} />
              )}
            </div>
          </div>
          <div className="fmtm-my-3">
            <div className="fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-mb-1">
              <p className="fmtm-body-sm-semibold fmtm-text-[#706E6E]">ID: #{data.id}</p>
              {data.visibility === 'PRIVATE' && (
                <Tooltip title="Private Project" arrow>
                  <AssetModules.LockOutlinedIcon className="fmtm-text-red-medium !fmtm-text-[12px]" />
                </Tooltip>
              )}
            </div>
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
            ADD A DESCRIPTION HERE
          </div>
        </div>
        {data.field_mapping_app !== field_mapping_app.QField && data.status !== project_status.DRAFT && (
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
        )}
      </div>
    </div>
  );
}
