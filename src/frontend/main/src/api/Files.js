import React, { useEffect, useState } from 'react';
import CoreModules from '../shared/CoreModules';

export const ProjectFilesById = (url, taskId) => {
  const [loading, setLoading] = useState(true);
  const [qrcode, setQrcode] = useState('');
  const source = CoreModules.axios.CancelToken.source();
  useEffect(() => {
    const fetchProjectFileById = async (url) => {
      try {
        setLoading(true);
        const fileJson = await CoreModules.axios.get(url, {
          cancelToken: source.token,
        });
        const resp = fileJson.data;
        const taskIndex = resp.project_tasks.findIndex((task) => task.id == taskId);
        const getQrcodeByIndex = resp.project_tasks[taskIndex].qr_code_base64;
        setQrcode(getQrcodeByIndex);
        setLoading(false);
      } catch (error) {
        setLoading(false);
      }
    };

    fetchProjectFileById(url);

    const cleanUp = () => {
      setLoading(false);
      setQrcode('');
      if (source) {
        source.cancel('component unmounted');
      }
    };

    return cleanUp;
  }, [taskId]);

  return { loading, qrcode };
};
