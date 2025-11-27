import React, { ChangeEvent, useEffect, useState } from 'react';
import { format } from 'date-fns';
import AssetModules from '@/shared/AssetModules';
import validateFileTypes from '@/utilfunctions/validateFileTypes';
import useCustomUpload from '@/hooks/useCustomUpload';
import { Input } from '@/components/RadixComponents/Input';
import { useAppDispatch } from '@/types/reduxTypes';
import { CommonActions } from '@/store/slices/CommonSlice';
import type { FieldValues, UseFormRegister, UseFormSetValue } from 'react-hook-form';
import { FileType } from '@/types';

type FileEvent = ChangeEvent<HTMLInputElement> & {
  target: EventTarget & { files: FileList };
};

type FileUploadProps = {
  name?: string;
  register?: UseFormRegister<FieldValues>;
  setValue?: UseFormSetValue<FieldValues>;
  multiple?: boolean;
  fileAccept?: string;
  data: FileType[] | string[];
  placeholder?: string;
  onChange?: (files: FileType[]) => void;
  onDelete?: (files: FileType[]) => void;
  showPreview?: boolean;
};

export default function FileUpload({
  name,
  register,
  setValue,
  multiple,
  fileAccept = 'image/*',
  data,
  placeholder,
  onChange,
  onDelete,
  showPreview = true,
}: FileUploadProps) {
  const dispatch = useAppDispatch();

  const [inputRef, onFileUpload] = useCustomUpload();
  const [uploadedFiles, setUploadedFiles] = useState<FileType[]>([]);

  // handling data when editing
  useEffect(() => {
    if (Array.isArray(data) && typeof data[0] === 'string') {
      const uploaded = (data as string[]).map((url) => ({
        id: crypto.randomUUID(),
        previewURL: url,
        file: { name: url.split('/').pop() || '' },
      }));
      setUploadedFiles(uploaded as FileType[]);
    }
  }, [data]);

  // handles data when file is upload
  useEffect(() => {
    if (Array.isArray(data) && typeof data[0] === 'object') {
      setUploadedFiles(data as FileType[]);
    }
  }, [data]);

  // register form element to useForm
  useEffect(() => {
    if (!register || !setValue || !name) return;
    register(name);
  }, [register, name, setValue]);

  const handleFileUpload = (event: FileEvent) => {
    const { files } = event.target;

    const isValidFile = validateFileTypes(files, fileAccept);

    if (!isValidFile) {
      dispatch(CommonActions.SetSnackBar({ message: 'Invalid file type' }));
      return;
    }

    const uploaded = Array.from(files).map((file) => ({
      id: crypto.randomUUID() as string,
      previewURL: file.type.startsWith('image/') ? URL.createObjectURL(file) : '',
      file,
    }));
    const uploadedFilesState = multiple ? [...uploadedFiles, ...uploaded] : uploaded;
    setUploadedFiles(uploadedFilesState);
    if (name && setValue) {
      setValue(name, uploadedFilesState, { shouldDirty: true });
    }
    onChange?.(uploadedFilesState);
  };

  // reset file input to allow re-upload after deletion
  const resetFileInput = () => {
    if (inputRef && 'current' in inputRef) {
      const fileInput = inputRef.current;
      if (fileInput) {
        fileInput.value = '';
      }
    }
  };

  const handleDeleteFile = (id: string) => {
    const updatedData = uploadedFiles.filter((file) => file.id !== id);
    setUploadedFiles(updatedData);
    if (name && setValue) {
      setValue(name, updatedData, { shouldDirty: true });
    }
    resetFileInput();
    onDelete?.(updatedData);
  };

  return (
    <div className="fmtm-flex fmtm-flex-col fmtm-gap-2">
      <div
        className="fmtm-flex fmtm-flex-col fmtm-cursor-pointer fmtm-items-center fmtm-justify-center fmtm-rounded-lg fmtm-border-2 fmtm-border-dashed fmtm-py-2.5"
        //   @ts-ignore
        onClick={onFileUpload}
      >
        <AssetModules.CloudUploadOutlinedIcon style={{ fontSize: '24px' }} className="fmtm-text-primaryRed" />
        <p className="fmtm-text-sm fmtm-text-grey-600">
          {placeholder || 'Please upload picture (jpeg, png file format)'}
        </p>
        <Input
          ref={inputRef}
          type="file"
          className="fmtm-hidden"
          multiple={multiple}
          onChange={handleFileUpload}
          accept={fileAccept}
        />
      </div>

      {showPreview && (
        <div className="fmtm-flex fmtm-flex-col fmtm-scrollbar fmtm-max-h-52 fmtm-overflow-auto">
          {uploadedFiles.map(({ file, id, previewURL }) => (
            <div key={id} className="flex items-center justify-between border p-2 rounded">
              <div className="fmtm-flex fmtm-gap-4 fmtm-items-center">
                {!previewURL ? (
                  <div className="fmtm-w-8 fmtm-h-8 fmtm-rounded-full fmtm-bg-red-light fmtm-flex fmtm-items-center fmtm-justify-center">
                    <AssetModules.DescriptionIcon className="!fmtm-text-[1.2rem] fmtm-text-blue-gray" />
                  </div>
                ) : (
                  <div className="fmtm-image-cover">
                    <img src={previewURL} width={40} alt="" />
                  </div>
                )}
                <div className="fmtm-flex fmtm-flex-col">
                  <h5 className="fmtm-max-w-40 fmtm-truncate fmtm-text-sm">{file?.name}</h5>
                  {file && file?.lastModifiedDate && (
                    <p className="fmtm-text-xs fmtm-text-grey-600">
                      Last modified on {format(new Date(file.lastModifiedDate), 'MMM dd yyyy')}
                    </p>
                  )}
                </div>
              </div>
              <div className="fmtm-flex fmtm-gap-3">
                <AssetModules.DeleteOutlinedIcon
                  className="fmtm-text-red-400 fmtm-cursor-pointer !fmtm-text-xl"
                  onClick={() => handleDeleteFile(id)}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
