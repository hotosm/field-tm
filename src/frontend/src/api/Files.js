import { useEffect, useState } from 'react';
import qrcodeGenerator from 'qrcode-generator';

export const ProjectFilesById = (odkToken, projectName, osmUser, taskId) => {
  const [qrcode, setQrcode] = useState('');
  useEffect(() => {
    const fetchProjectFileById = async (odkToken, projectName, osmUser, taskId) => {
      if (!taskId || odkToken === '') {
        setQrcode('');
        return;
      }

      const odkCollectJson = JSON.stringify({
        general: {
          server_url: odkToken,
          form_update_mode: 'manual',
          basemap_source: 'osm',
          autosend: 'wifi_and_cellular',
          metadata_username: osmUser,
          metadata_email: taskId,
        },
        project: { name: projectName },
        admin: {},
      });

      // Note: error correction level = "L"
      const code = qrcodeGenerator(0, 'L');
      // Note: btoa base64 encodes the JSON string
      code.addData(btoa(odkCollectJson));
      code.make();

      // Note: cell size = 3, margin = 5
      setQrcode(code.createDataURL(3, 5));
    };

    fetchProjectFileById(odkToken, projectName, osmUser, taskId);

    const cleanUp = () => {
      setQrcode('');
    };

    return cleanUp;
  }, [taskId]);
  return { qrcode };
};
