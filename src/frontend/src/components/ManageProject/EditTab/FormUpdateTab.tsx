import React, { useState } from 'react';
import UploadArea from '../../common/UploadArea';
import Button from '../../common/Button';
import CoreModules from '@/shared/CoreModules';
import { PostFormUpdate } from '@/api/CreateProjectService';

type FileType = {
  id: string;
  name: string;
  url?: File;
  isDeleted: boolean;
};

const FormUpdateTab = ({ projectId }) => {
  const dispatch = CoreModules.useAppDispatch();

  const [uploadForm, setUploadForm] = useState<FileType[] | null>(null);

  const onSave = () => {
    dispatch(
      PostFormUpdate(`${import.meta.env.VITE_API_URL}/projects/update_category`, {
        project_id: projectId,
        upload: uploadForm && uploadForm?.[0]?.url,
      }),
    );
  };

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-10">
      <UploadArea
        title="Upload Form"
        label="Please upload .xls, .xlsx, .xml file"
        multiple={false}
        data={uploadForm || []}
        filterKey="url"
        onUploadFile={(updatedFiles) => {
          setUploadForm(updatedFiles);
        }}
        acceptedInput=".xls, .xlsx, .xml"
      />
      <div className="fmtm-flex fmtm-justify-center">
        <Button onClick={onSave} btnText="UPDATE" btnType="primary" className="fmtm-rounded-md" />
      </div>
    </div>
  );
};

export default FormUpdateTab;
