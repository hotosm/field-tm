import { useEffect, useState } from 'react';
import qrcodeGenerator from 'qrcode-generator';
import { deflate } from 'pako/lib/deflate';

// function base64zlibdecode(string) {
//   return new TextDecoder().decode(inflate(Uint8Array.from(window.atob(string), (c) => c.codePointAt(0))))
// }

function base64zlibencode(string: string) {
  return window.btoa(String.fromCodePoint(...deflate(new TextEncoder().encode(string))));
}

export const GetProjectQrCode = (
  odkToken: string | undefined,
  projectName: string | undefined,
  osmUser: string,
): { qrcode: string } => {
  const [qrcode, setQrcode] = useState('');

  useEffect(() => {
    const fetchProjectFileById = async (
      odkToken: string | undefined,
      projectName: string | undefined,
      osmUser: string,
    ) => {
      if (!odkToken || !projectName) {
        setQrcode('');
        return;
      }

      const odkCollectJson = JSON.stringify({
        general: {
          server_url: odkToken,
          form_update_mode: 'match_exactly',
          basemap_source: 'osm',
          autosend: 'wifi_and_cellular',
          metadata_email: 'NOT IMPLEMENTED',
          metadata_username: osmUser,
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

    fetchProjectFileById(odkToken, projectName, osmUser);
  }, [projectName, odkToken, osmUser]);
  return { qrcode };
};

export const GetQfieldProjectQrCode = (id: string | null | undefined): { qrcode: string } => {
  const [qrcode, setQrcode] = useState('');

  useEffect(() => {
    const fetchProjectFileById = async (id: string | null | undefined) => {
      if (!id) {
        setQrcode('');
        return;
      }
      const code = qrcodeGenerator(0, 'L');
      code.addData(`qfield://cloud?project=${id}`);
      code.make();
      setQrcode(code.createDataURL(6, 5));
    };

    fetchProjectFileById(id);
  }, [id]);
  return { qrcode };
};
