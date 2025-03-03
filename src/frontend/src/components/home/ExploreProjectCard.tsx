import * as React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch } from '@/types/reduxTypes';
import CustomizedImage from '@/utilities/CustomizedImage';
import CustomizedProgressBar from '@/utilities/CustomizedProgressBar';
import { HomeActions } from '@/store/slices/HomeSlice';
import { projectType } from '@/models/home/homeModel';
import CoreModules from '@/shared/CoreModules';
import AssetModules from '@/shared/AssetModules';

export default function ExploreProjectCard({ data }: { data: projectType }) {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  const handleProjectCardClick = () => {
    const project: projectType = data;
    dispatch(HomeActions.SetSelectedProject(project));
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
            <p>#{data.id}</p>
          </div>

          <div className="fmtm-flex fmtm-flex-col fmtm-justify-start fmtm-mt-[2%]">
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
          </div>
        </div>
        <div>
          <div className="fmtm-flex fmtm-items-center fmtm-gap-1 fmtm-mt-[7%] fmtm-ml-[2%]">
            <p className="fmtm-text-2xl fmtm-font-bold">{data.num_contributors}</p>
            <p className="fmtm-text-lg">{data.num_contributors === 1 ? 'contributor' : 'contributors'}</p>
          </div>
          <CustomizedProgressBar data={data} height={7} />
        </div>
      </div>
    </div>
  );
}
