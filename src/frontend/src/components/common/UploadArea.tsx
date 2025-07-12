import React, { useEffect, useRef, useState } from 'react';
import { CommonActions } from '@/store/slices/CommonSlice';
import AssetModules from '@/shared/AssetModules';
import { useAppDispatch } from '@/types/reduxTypes';
import { convertFileUrlToFileArray } from '@/utilfunctions';
import isEmpty from '@/utilfunctions/isEmpty';

type FileType =
  | {
      id: string;
      file: File;
      previewURL: string;
    }
  | { id: string; file: { name: string }; previewURL: string };

type uploadAreaPropType = {
  title?: string;
  label: string;
  data: FileType[] | string;
  onUploadFile: (updatedFiles: FileType[], ref: React.RefObject<HTMLInputElement | null>) => void;
  acceptedInput: string;
};

const UploadArea = ({ title, label, acceptedInput, data, onUploadFile }: uploadAreaPropType) => {
  const dispatch = useAppDispatch();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFiles, setSelectedFiles] = useState<FileType[]>([]);

  useEffect(() => {
    let uploaded: [] = [];
    if (!data) return;
    // @ts-ignore
    if (data && typeof data?.[0] !== 'string') {
      uploaded = data as [];
    } else {
      uploaded = convertFileUrlToFileArray(data as string) as [];
    }
    // @ts-ignore
    setSelectedFiles(uploaded);
  }, [data]);

  const handleOpenFileExplorer = () => {
    fileInputRef?.current?.click();
  };

  const changeHandler = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { files } = event.target;
    if (!files) return;
    const fileList = Object.values(files).map((fileItem) => {
      const file = fileItem;
      const id = crypto.randomUUID();
      return { id, file: file, previewURL: URL.createObjectURL(file) };
    });
    onUploadFile(fileList, fileInputRef);
  };

  const handleDeleteFile = (id: string) => {
    const updatedList = selectedFiles.filter((item: FileType) => item.id !== id);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    return onUploadFile(updatedList, fileInputRef);
  };

  return (
    <div>
      {title && <p className="fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold">{title}</p>}
      <div
        role="button"
        tabIndex={0}
        onKeyDown={() => {}}
        onClick={handleOpenFileExplorer}
        onDragEnter={(e) => {
          e.stopPropagation();
          e.preventDefault();
        }}
        onDragOver={(e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'copy';
        }}
        onDrop={(e) => {
          e.preventDefault();
          if (!isEmpty(e.dataTransfer.files)) {
            const { files } = e.dataTransfer;
            const fileList: FileType[] = [];
            Object.values(files).map((item) => {
              const file = item;
              const fileType = file.name.split('.')?.pop();
              if (acceptedInput === 'all') {
                const id = crypto.randomUUID();
                return fileList.push({ id, file, previewURL: URL.createObjectURL(file) });
              }
              if (fileType && acceptedInput.includes(fileType)) {
                const id = crypto.randomUUID();
                return fileList.push({ id, file, previewURL: URL.createObjectURL(file) });
              }
              dispatch(
                CommonActions.SetSnackBar({
                  message: 'Invalid File Type.',
                }),
              );
              return null;
            });
            if (fileList.length > 0) {
              onUploadFile([fileList.at(fileList.length - 1) as FileType], fileInputRef);
            } else {
              onUploadFile(data as FileType[], fileInputRef);
            }
          }
        }}
        className="fmtm-cursor-pointer fmtm-border-[1px] fmtm-border-[#D8D8D8] fmtm-border-dashed fmtm-rounded-md fmtm-flex fmtm-flex-col fmtm-gap-1 fmtm-py-2 focus:fmtm-border-[#D73F37] focus:fmtm-ring-[#D73F37]/50 focus:fmtm-ring-[3px]"
      >
        <input
          className="fmtm-hidden"
          ref={fileInputRef}
          type="file"
          accept={acceptedInput === 'all' ? '' : acceptedInput}
          onChange={changeHandler}
        />
        <div className="fmtm-flex fmtm-justify-center">
          <AssetModules.CloudUploadOutlinedIcon style={{ fontSize: '24px' }} className="fmtm-text-primaryRed" />
        </div>
        <p className="fmtm-body-md fmtm-text-center fmtm-text-grey-600">{label}</p>
      </div>
      {selectedFiles?.length > 0 && (
        <div className="fmtm-mt-2 fmtm-w-full">
          {selectedFiles?.map((item, i) => (
            <div key={item.id} className="fmtm-flex fmtm-items-center fmtm-w-full">
              {acceptedInput.includes('image') ? (
                <img src={item.previewURL} className="fmtm-h-full fmtm-z-50" />
              ) : (
                <div className="fmtm-w-8 fmtm-h-8 fmtm-rounded-full fmtm-bg-red-light fmtm-flex fmtm-items-center fmtm-justify-center">
                  <AssetModules.DescriptionIcon className="!fmtm-text-[1.2rem] fmtm-text-[#4C4C4C]" />
                </div>
              )}
              <div
                className="fmtm-flex-1 fmtm-text-ellipsis fmtm-truncate fmtm-ml-4 fmtm-text-sm"
                title={item?.file?.name}
              >
                {item?.file?.name}
              </div>
              <div className="fmtm-flex">
                <div
                  role="button"
                  tabIndex={0}
                  onKeyDown={() => {}}
                  onClick={() => handleDeleteFile(item.id)}
                  className="fmtm-px-4"
                >
                  <AssetModules.DeleteIcon className="fmtm-text-grey-400 hover:fmtm-text-[#FF4538] !fmtm-text-[1.2rem]" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UploadArea;
