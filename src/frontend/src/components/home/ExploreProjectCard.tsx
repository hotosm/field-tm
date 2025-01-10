import * as React from 'react';
import CustomizedImage from '@/utilities/CustomizedImage';
import CustomizedProgressBar from '@/utilities/CustomizedProgressBar';
import { HomeActions } from '@/store/slices/HomeSlice';
import { projectType } from '@/models/home/homeModel';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import { useNavigate } from 'react-router-dom';

//Explore Project Card Model to be rendered in home view
export default function ExploreProjectCard({ data }: { data: projectType }) {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  const defaultTheme = useAppSelector((state) => state.theme.hotTheme);

  return (
    <div
      onClick={() => {
        const project: projectType = data;
        dispatch(HomeActions.SetSelectedProject(project));
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        if (isMobile) {
          window.location.href = `/mapnow/${data.id}`;
        } else {
          navigate(`/project/${data.id}`);
        }
      }}
      className="hover:fmtm-bg-red-50 hover:fmtm-shadow-xl fmtm-duration-500 fmtm-rounded-lg fmtm-border-[1px] fmtm-border-solid fmtm-border-[#706E6E] fmtm-bg-white fmtm-p-4 fmtm-max-h-fit fmtm-cursor-pointer"
    >
      <div className="fmtm-flex fmtm-flex-col fmtm-justify-between fmtm-h-full">
        <div>
          <div className="fmtm-flex fmtm-justify-between">
            {data.organisation_logo ? (
              <div className="fmtm-h-[50px]">
                <CoreModules.CardMedia component="img" src={data.organisation_logo} sx={{ height: 50 }} />
              </div>
            ) : (
              <CustomizedImage status={'card'} style={{ width: 50, height: 50 }} />
            )}
            <CoreModules.Typography variant="h4" right={7} top={5} gutterBottom>
              #{data.id}
            </CoreModules.Typography>
          </div>

          {/*Project Info and description*/}
          <CoreModules.Stack direction={'column'} mt={'2%'} justifyContent={'left'}>
            <p className="fmtm-line-clamp-3 fmtm-text-xl fmtm-capitalize fmtm-font-bold" title={data.name}>
              {data.name}
            </p>

            <p
              className="fmtm-capitalize fmtm-line-clamp-2 fmtm-mt-[5%] fmtm-text-[#7A7676]"
              title={data.short_description}
            >
              {data.short_description}
            </p>
            <div className="fmtm-flex fmtm-items-start fmtm-mt-[1.63rem] fmtm-gap-2">
              <AssetModules.LocationOn color="error" style={{ fontSize: '22px' }} />
              <p className="fmtm-capitalize fmtm-line-clamp-1 fmtm-text-[#7A7676]" title={data?.location_str}>
                {data?.location_str || '-'}
              </p>
            </div>
          </CoreModules.Stack>
        </div>
        <div>
          {/* Number of Contributors */}
          <CoreModules.Stack direction={'row'}>
            <CoreModules.Typography
              mt={'7%'}
              ml={'2%'}
              variant="h2"
              fontSize={defaultTheme.typography.subtitle1.fontSize}
              fontWeight={'bold'}
              color="info"
            >
              {data.num_contributors}
            </CoreModules.Typography>

            <CoreModules.Typography
              mt={'8%'}
              ml={'2%'}
              variant="h2"
              fontSize={defaultTheme.typography.htmlFontSize}
              color="info"
            >
              contributor{data.num_contributors === 1 ? '' : 's'}
            </CoreModules.Typography>
          </CoreModules.Stack>

          {/* Contribution Progress Bar */}
          <CustomizedProgressBar data={data} height={7} />
        </div>
      </div>
    </div>
  );
}
