import React, { useEffect, useRef, useState } from 'react';
import { useDispatch } from 'react-redux';
import { CommonActions } from '@/store/slices/CommonSlice';
import AssetModules from '@/shared/AssetModules';
import { v4 as uuidv4 } from 'uuid';

type FileType = {
  id: string;
  name: string;
  url?: File;
  isDeleted: boolean;
};

type uploadAreaPropType = {
  title: string;
  label: string;
  multiple: boolean;
  data: FileType[];
  filterKey: string;
  onUploadFile: (updatedFiles: FileType[]) => void;
  acceptedInput: string;
};

const UploadArea = ({ title, label, acceptedInput, data, onUploadFile, multiple, filterKey }: uploadAreaPropType) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dispatch = useDispatch();
  const [selectedFiles, setSelectedFiles] = useState<FileType[]>([]);

  function isEmpty(obj) {
    if (Array.isArray(obj)) {
      return obj.length === 0;
    }
    return Object.keys(obj).length === 0;
  }

  const handleOpenFileExplorer = () => {
    fileInputRef?.current?.click();
  };
  useEffect(() => {
    setSelectedFiles(data);
  }, [data]);

  const changeHandler = (event) => {
    const { files } = event.target;
    const fileList = Object.values(files).map((item: any) => {
      const { name } = item;
      const file = item;
      const id = uuidv4();
      const isDeleted = false;
      return { id, name, [filterKey]: file, isDeleted };
    });
    if (multiple) {
      onUploadFile([...fileList, ...data]);
    } else {
      onUploadFile(fileList);
    }
  };
  const handleDeleteFile = (id: string) => {
    const updatedList = data.filter((item: FileType) => item.id !== id);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    return onUploadFile(updatedList);
  };

  return (
    <div>
      <p className="fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold ">{title}</p>
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
              const { name } = item;
              const file = item;
              const fileType = file.name.split('.')?.pop();
              if (acceptedInput === 'all') {
                const isDeleted = false;
                const id = uuidv4();
                return fileList.push({ id, name, [filterKey]: file, isDeleted });
              }
              if (fileType && acceptedInput.includes(fileType)) {
                const id = uuidv4();
                const isDeleted = false;
                return fileList.push({ id, name, [filterKey]: file, isDeleted });
              }
              dispatch(
                CommonActions.SetSnackBar({
                  open: true,
                  message: 'Invalid File Type.',
                  variant: 'error',
                  duration: 2000,
                }),
              );
              return null;
            });
            if (fileList.length > 0) {
              if (multiple) {
                onUploadFile([...fileList, ...data]);
              } else {
                onUploadFile([fileList.at(fileList.length - 1) as FileType]);
              }
            } else {
              onUploadFile(data);
            }
          }
        }}
        className="fmtm-cursor-pointer fmtm-border-[1px] fmtm-border-[#D8D8D8] fmtm-border-dashed fmtm-rounded-md fmtm-flex fmtm-flex-col fmtm-gap-2 fmtm-py-4"
      >
        <input
          className="fmtm-hidden"
          ref={fileInputRef}
          type="file"
          accept={acceptedInput === 'all' ? '' : acceptedInput}
          multiple={multiple}
          onChange={changeHandler}
        />
        <div className="fmtm-flex fmtm-justify-center">
          <AssetModules.CloudUploadOutlinedIcon style={{ fontSize: '32px' }} className="fmtm-text-primaryRed" />
        </div>
        <div className="fmtm-text-body-md fmtm-text-center fmtm-text-sm fmtm-text-[#757575] fmtm-font-archivo fmtm-font-semibold fmtm-tracking-wide">
          {label}
        </div>
      </div>
      {selectedFiles?.length > 0 && (
        <div className="fmtm-overflow-hidden fmtm-overflow-y-scroll scrollbar fmtm-h-fit">
          {selectedFiles?.map((item, i) => (
            <div
              key={item.id}
              className="fmtm-px-3 fmtm-flex fmtm-items-center fmtm-relative fmtm-border-b-regular fmtm-border-border_color"
            >
              <div className="fmtm-h-10 fmtm-w-10 fmtm-rounded-full fmtm-bg-active_bg fmtm-border-regular fmtm-p-2 fmtm-mr-2 fmtm-border-border_color ">
                <AssetModules.DescriptionIcon className="fmtm-text-active_text" />
              </div>
              <div className="fmtm-py-3 fmtm-pr-2 fmtm-w-5/6">
                <div className="fmtm-text-button-1 fmtm-w-full fmtm-text-ellipsis">{item.name}</div>
              </div>
              <div className="fmtm-flex fmtm-absolute fmtm-right-3">
                <div
                  role="button"
                  tabIndex={0}
                  onKeyDown={() => {}}
                  onClick={() => handleDeleteFile(item.id)}
                  className="fmtm-h-10 fmtm-w-10 fmtm-p-2"
                >
                  <AssetModules.DeleteIcon className="fmtm-text-[#FF4538]" />
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
