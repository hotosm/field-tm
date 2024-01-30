import { useEffect, useState } from 'react';
import qrcodeGenerator from 'qrcode-generator';

export const ProjectFilesById = (odkToken, projectName, osmUser, taskId) => {
  const [loading, setLoading] = useState(true);
  const [qrcode, setQrcode] = useState('');
  useEffect(() => {
    const fetchProjectFileById = async (odkToken, projectName, osmUser, taskId) => {
      setLoading(true);

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
      setLoading(false);
    };

    fetchProjectFileById(odkToken, projectName, osmUser, taskId);

    const cleanUp = () => {
      setLoading(false);
      setQrcode('');
    };

    return cleanUp;
  }, [taskId]);
  return { loading, qrcode };
};
