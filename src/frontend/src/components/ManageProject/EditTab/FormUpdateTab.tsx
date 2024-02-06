import React, { useEffect, useState } from 'react';
import UploadArea from '../../common/UploadArea';
import { CustomSelect } from '../../common/Select';
import Button from '../../common/Button';
import CoreModules from '@/shared/CoreModules';
import { diffObject } from '@/utilfunctions/compareUtils.js';
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
  const [selectedFormCategory, setSelectedFormCategory] = useState<string | null>(null);
  const formCategoryList = CoreModules.useAppSelector((state) => state.createproject.formCategoryList);
  const previousXform_title = CoreModules.useAppSelector((state) => state.project.projectInfo.xform_title);

  useEffect(() => {
    setSelectedFormCategory(previousXform_title);
  }, [previousXform_title]);

  const onSave = () => {
    const diffPayload = diffObject({ category: previousXform_title }, { category: selectedFormCategory });
    dispatch(
      PostFormUpdate(`${import.meta.env.VITE_API_URL}/projects/update_category`, {
        ...(Object.keys(diffPayload).length > 0 ? diffPayload : { category: selectedFormCategory }),
        project_id: projectId,
        upload: uploadForm && uploadForm?.[0]?.url,
      }),
    );
  };

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-10">
      <CustomSelect
        title="Form Category"
        placeholder="Choose"
        data={formCategoryList}
        dataKey="title"
        value={selectedFormCategory}
        valueKey="title"
        label="title"
        onValueChange={(value) => value && setSelectedFormCategory(value?.toString())}
        className="fmtm-bg-white"
      />
      <UploadArea
        title="Upload Form"
        label="Please upload .xls, .slxs, .xml file"
        multiple={false}
        data={uploadForm || []}
        filterKey="url"
        onUploadFile={(updatedFiles) => {
          setUploadForm(updatedFiles);
        }}
        acceptedInput=".xls, .slxs, .xml"
      />
      <div className="fmtm-flex fmtm-justify-center">
        <Button onClick={onSave} btnText="UPDATE" btnType="primary" className="fmtm-rounded-md" />
      </div>
    </div>
  );
};

export default FormUpdateTab;
