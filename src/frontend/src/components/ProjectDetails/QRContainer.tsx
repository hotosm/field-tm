import React from 'react';
import { projectInfoType } from '@/models/project/projectModel';
import { field_mapping_app } from '@/types/enums';
import { GetProjectQrCode, GetQfieldProjectQrCode } from '@/api/Files';
import { useAppSelector } from '@/types/reduxTypes';
import Button from '@/components/common/Button';
import AssetModules from '@/shared/AssetModules';
import { useParams } from 'react-router-dom';

type QRContainerPropsType = {
  projectInfo: Partial<projectInfoType>;
};

const QRContainer = ({ projectInfo }: QRContainerPropsType) => {
  const params = useParams();
  const projectId = params.id;

  // @ts-ignore
  const authDetails = useAppSelector((state) => state?.login?.authDetails);

  const { qrcode: qfieldQR } = GetQfieldProjectQrCode(projectInfo?.qfield_project_id);
  const { qrcode: odkQR } = GetProjectQrCode(projectInfo?.odk_token, projectInfo?.name, authDetails?.osm_user);
  const downloadQr = () => {
    const downloadLink = document.createElement('a');
    downloadLink.href = projectInfo.field_mapping_app === field_mapping_app.ODK ? odkQR : qfieldQR;
    downloadLink.download = `${projectInfo.field_mapping_app}_project_${projectId}.png`;
    downloadLink.click();
  };

  return (
    <div>
      {projectInfo.field_mapping_app !== field_mapping_app.FieldTM &&
        ((projectInfo?.field_mapping_app === field_mapping_app.QField && projectInfo?.qfield_project_id) ||
          projectInfo?.field_mapping_app === field_mapping_app.ODK) && (
          <div className="fmtm-flex fmtm-flex-col fmtm-items-center fmtm-bg-white fmtm-w-fit fmtm-mx-auto fmtm-p-4 fmtm-rounded-md fmtm-gap-2">
            <p className="fmtm-font-medium">Scan this QR via {projectInfo.field_mapping_app} to load the project</p>
            {projectInfo?.field_mapping_app === field_mapping_app.QField && projectInfo?.qfield_project_id ? (
              <img src={qfieldQR} alt="QField QR" />
            ) : projectInfo?.field_mapping_app === field_mapping_app.ODK ? (
              <img src={odkQR} alt="ODK QR" />
            ) : (
              <></>
            )}
            <Button variant="link-red" onClick={downloadQr}>
              <AssetModules.FileDownloadOutlinedIcon className="!fmtm-text-[20px]" /> Download QR
            </Button>
          </div>
        )}
    </div>
  );
};

export default QRContainer;
