import React, { useEffect, useRef, useState } from 'react';
import Button from '@/components/common/Button';
import AssetModules from '@/shared/AssetModules';
import boltIcon from '@/assets/icons/boltIcon.svg';
import ODKLogo from '@/assets/images/odk-logo.svg';
import { Tooltip } from '@mui/material';

const ProjectDetailsV2 = () => {
  const paraRef = useRef<HTMLParagraphElement>(null);

  const [seeMore, setSeeMore] = useState(false);
  const [descLines, setDescLines] = useState(1);

  useEffect(() => {
    if (paraRef.current) {
      const lineHeight = parseFloat(getComputedStyle(paraRef.current).lineHeight);
      const lines = Math.floor(paraRef.current.clientHeight / lineHeight);
      setDescLines(lines);
    }
  }, [paraRef.current]);
  return (
    <div>
      <div className="fmtm-max-w-7xl fmtm-bg-white fmtm-border-b fmtm-border-border fmtm-px-6 fmtm-py-4 fmtm-rounded-lg fmtm-mx-auto fmtm-mt-2">
        <div className="fmtm-flex fmtm-items-center fmtm-justify-between fmtm-gap-5 fmtm-flex-wrap lg:fmtm-flex-nowrap">
          <div className="fmtm-flex fmtm-items-center fmtm-gap-3">
            <button className="fmtm-p-1 hover:fmtm-bg-red-light hover:fmtm-text-red-medium fmtm-duration-100 fmtm-w-8 fmtm-h-8 fmtm-flex fmtm-justify-center fmtm-items-center fmtm-rounded-lg">
              <AssetModules.ChevronLeftIcon className="fmtm-w-5 fmtm-h-5" />
            </button>
            <h4>
              Cameroon Test Test Test
              <Tooltip title={`Project created using ODK`} arrow className="fmtm-cursor-pointer">
                <img
                  src={ODKLogo}
                  className="fmtm-inline-block fmtm-h-5 fmtm-max-h-5 fmtm-align-middle fmtm-ml-2"
                  alt="qfield logo"
                />
              </Tooltip>
            </h4>
          </div>
          <div className="fmtm-flex fmtm-items-center fmtm-gap-3 fmtm-ml-auto">
            <Button variant="secondary-grey" className="fmtm-gap-2">
              <img src={boltIcon} alt="bolt icon" />
              Generate Basemap
            </Button>
            <Button variant="secondary-grey" className="fmtm-gap-2">
              <AssetModules.FileDownloadOutlinedIcon className="!fmtm-w-5 !fmtm-h-5" />
              Download XLS FORM
            </Button>
          </div>
        </div>
      </div>

      <div className="fmtm-max-w-7xl fmtm-mx-auto fmtm-mt-4">
        <div className="fmtm-grid fmtm-grid-cols-1 lg:fmtm-grid-cols-2 fmtm-gap-8">
          <div className="fmtm-flex fmtm-flex-col fmtm-gap-6">
            <div className="fmtm-p-6 fmtm-border-b fmtm-border-border fmtm-border-0 fmtm-bg-white fmtm-rounded-lg">
              <div className="fmtm-space-y-6">
                <div>
                  <h4 className="fmtm-text-[#D4183D] fmtm-mb-3">Description</h4>
                  <div>
                    <p
                      className={`${!seeMore ? 'fmtm-line-clamp-[7]' : ''} fmtm-body-md fmtm-text-grey-900 `}
                      ref={paraRef}
                    >
                      Lorem ipsum, dolor sit amet consectetur adipisicing elit. Deleniti maiores exercitationem,
                      aspernatur laborum quae velit eaque omnis autem esse. Quisquam, similique obcaecati! Repudiandae
                      error, itaque adipisci cum optio dolore doloremque corrupti totam fugiat aperiam, eveniet autem
                      enim quibusdam odit voluptates. Lorem ipsum dolor sit amet consectetur adipisicing elit. Eius
                      excepturi aliquam impedit consectetur cumque molestias rerum at cupiditate nostrum eos veritatis
                      necessitatibus provident atque neque, similique, reprehenderit voluptatem, numquam laudantium
                      ullam? Nobis, incidunt eos illum ipsam veritatis non magnam deleniti dolor quaerat modi amet
                      accusamus provident officiis odit tenetur labore! Eius excepturi aliquam impedit consectetur
                      cumque molestias rerum at cupiditate nostrum eos veritatis necessitatibus provident atque neque,
                      similique, reprehenderit voluptatem, numquam laudantium ullam? Nobis, incidunt eos illum ipsam
                      veritatis non magnam deleniti dolor quaerat modi amet accusamus provident officiis odit tenetur
                      labore!
                    </p>
                    {descLines >= 7 && (
                      <p
                        className="fmtm-body-md fmtm-text-red-medium hover:fmtm-text-red-dark hover:fmtm-cursor-pointer fmtm-w-fit"
                        onClick={() => setSeeMore(!seeMore)}
                      >
                        ... {!seeMore ? 'See More' : 'See Less'}
                      </p>
                    )}
                  </div>
                </div>
                <div className="fmtm-border-t" />
                <div className="fmtm-grid fmtm-grid-cols-2 fmtm-gap-6">
                  <div>
                    <div className="fmtm-text-sm fmtm-text-gray-500 fmtm-mb-1">Project ID</div>
                    <div className="fmtm-text-sm fmtm-px-3 fmtm-py-1 fmtm-bg-gray-100 fmtm-w-fit fmtm-font-semibold fmtm-rounded-lg">
                      #19
                    </div>
                  </div>
                  <div>
                    <div className="fmtm-text-sm fmtm-text-gray-500 fmtm-mb-1">Project Location</div>
                    <div className="fmtm-flex fmtm-items-center fmtm-gap-1 fmtm-text-gray-900">
                      <AssetModules.PlaceOutlinedIcon className="!fmtm-text-xl fmtm-text-[#D4183D]" />
                      <span>Accra, Ghana</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="fmtm-p-6 fmtm-border-b fmtm-border-border fmtm-border-0 fmtm-bg-white fmtm-rounded-lg">
              <div className="fmtm-space-y-4">
                <h4 className="fmtm-text-gray-900">ODK Username & Password</h4>
                <div className="fmtm-grid fmtm-grid-cols-2 fmtm-gap-3">
                  <Button
                    variant="secondary-grey"
                    className="fmtm-w-full fmtm-justify-start fmtm-gap-2 hover:fmtm-bg-gray-50"
                  >
                    <AssetModules.ContentCopyIcon className="!fmtm-text-sm" />
                    Copy Username
                  </Button>
                  <Button
                    variant="secondary-grey"
                    className="fmtm-w-full fmtm-justify-start fmtm-gap-2 hover:fmtm-bg-gray-50"
                  >
                    <AssetModules.ContentCopyIcon className="!fmtm-text-sm" />
                    Copy Password
                  </Button>
                </div>
              </div>
            </div>
            <div className="fmtm-w-full">
              <Button variant="secondary-red" className="fmtm-flex-1 fmtm-gap-2 hover:fmtm-bg-gray-50 fmtm-w-full">
                <AssetModules.OpenInNewIcon className="!fmtm-text-sm" />
                Manage Project in ODK Central
              </Button>
            </div>
          </div>

          <div className="fmtm-space-y-6">
            <div className="fmtm-p-8 fmtm-border-b fmtm-border-border fmtm-border-0 fmtm-bg-white fmtm-rounded-lg">
              <div className="fmtm-text-center fmtm-space-y-6">
                <div>
                  <h4 className="fmtm-text-gray-900 fmtm-mb-2">Scan QR Code</h4>
                  <p className="fmtm-text-sm fmtm-text-gray-500">
                    Scan this code with ODK Collect app to access the project
                  </p>
                </div>

                <div className="fmtm-flex fmtm-justify-center">
                  <div className="fmtm-bg-white fmtm-p-6 fmtm-rounded-2xl fmtm-border-b fmtm-border-border fmtm-border-2 fmtm-border-gray-100">
                    <div className="fmtm-bg-white fmtm-p-4 fmtm-rounded-lg">
                      <svg viewBox="0 0 400 400" className="fmtm-w-80 fmtm-h-80">
                        <rect width="400" height="400" fill="white" />
                        <rect x="20" y="20" width="120" height="120" fill="none" stroke="black" strokeWidth="16" />
                        <rect x="52" y="52" width="56" height="56" fill="black" />
                        <rect x="260" y="20" width="120" height="120" fill="none" stroke="black" strokeWidth="16" />
                        <rect x="292" y="52" width="56" height="56" fill="black" />
                        <rect x="20" y="260" width="120" height="120" fill="none" stroke="black" strokeWidth="16" />
                        <rect x="52" y="292" width="56" height="56" fill="black" />
                      </svg>
                    </div>
                  </div>
                </div>

                <Button variant="primary-red" className="fmtm-w-full">
                  <AssetModules.FileDownloadOutlinedIcon className="!fmtm-text-xl" />
                  Download QR
                </Button>

                <div className="fmtm-pt-4 fmtm-border-t fmtm-border-gray-100">
                  <div className="fmtm-text-xs fmtm-text-gray-400 fmtm-space-y-1">
                    <p>Compatible with ODK Collect App</p>
                    <p className="fmtm-text-gray-300">Project ID: #19 • Location: Accra, Ghana</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetailsV2;
