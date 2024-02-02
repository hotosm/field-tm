import { useEffect, useState } from 'react';
import qrcodeGenerator from 'qrcode-generator';
import { deflate } from 'pako/lib/deflate';

// function base64zlibdecode(string) {
//   return new TextDecoder().decode(inflate(Uint8Array.from(window.atob(string), (c) => c.codePointAt(0))))
// }

function base64zlibencode(string) {
  return window.btoa(String.fromCodePoint(...deflate(new TextEncoder().encode(string))));
}

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
          metadata_email: taskId.toString(),
        },
        project: { name: projectName },
        admin: {},
      });

      // Note: error correction level = "L"
      const code = qrcodeGenerator(0, 'L');
      // Note: btoa base64 encodes the JSON string
      // Note: pako.deflate zlib encodes to content
      code.addData(base64zlibencode(odkCollectJson));
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
