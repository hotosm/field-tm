import React, { useEffect, useRef, useState } from 'react';
import FmtmLogo from '@/assets/images/hotLog.png';

type bottomSheetType = {
  body: React.ReactElement;
  onClose: () => void;
};

const BottomSheet = ({ body, onClose }: bottomSheetType) => {
  const sheetContentRef: any = useRef(null);
  const bottomSheetRef: any = useRef(null);
  const logoRef: any = useRef(null);
  const [startY, setStartY] = useState(0);
  const [startHeight, setStartHeight] = useState(0);
  const [currSheetHeight, setCurrSheetHeight] = useState(0);
  const [show, setShow] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);

  useEffect(() => {
    setShow(true);
    document.body.style.overflowY = 'hidden';
    bottomSheetRef.current.style.height = `51vh`;
    updateSheetHeight(50);
  }, []);

  const updateSheetHeight = (height: number) => {
    if (sheetContentRef.current) {
      sheetContentRef.current.style.height = `${height}vh`;
      const top = sheetContentRef.current.getBoundingClientRect().top;
      const logoHeight = logoRef.current.getBoundingClientRect().height;
      logoRef.current.style.top = `${top - logoHeight}px`;
    }
    if (height === 100) {
      setIsFullScreen(true);
    } else {
      setIsFullScreen(false);
    }
  };

  const hideBottomSheet = () => {
    setShow(false);

    onClose();
    document.body.style.overflowY = 'auto';
  };

  const dragStart = (e) => {
    const pagesY = e.pageY || e.changedTouches[0].screenY;
    setStartY(pagesY);
    setStartHeight(parseInt(sheetContentRef.current.style.height));

    setIsDragging(true);
  };

  const dragging = (e) => {
    const delta = startY - (e.pageY || e.changedTouches[0].screenY);
    const newHeight = startHeight + (delta / window.innerHeight) * 100;
    bottomSheetRef.current.style.height = `100vh`;
    updateSheetHeight(newHeight);
  };

  const dragStop = () => {
    let sheetHeight;
    bottomSheetRef.current.style.height = `${currSheetHeight + 1}vh`;

    setIsDragging(false);
    sheetHeight = parseInt(sheetContentRef.current.style.height);
    setCurrSheetHeight(sheetHeight);

    sheetHeight < 25 ? hideBottomSheet() : sheetHeight > 75 ? updateSheetHeight(93) : updateSheetHeight(50);
  };

  useEffect(() => {
    dragStop();
  }, [currSheetHeight]);

  return (
    <div className="fmtm-absolute fmtm-bottom-[200px] fmtm-bg-white sm:fmtm-hidden fmtm-z-[10005]">
      <div
        className={`bottom-sheet fmtm-fixed fmtm-w-full fmtm-left-0 fmtm-bottom-0 fmtm-flex fmtm-items-center fmtm-flex-col fmtm-justify-end fmtm-duration-100 fmtm-ease-linear ${
          !show ? 'fmtm-opacity-0 fmtm-pointer-events-none' : 'fmtm-opacity-100 fmtm-pointer-events-auto'
        }`}
        ref={bottomSheetRef}
      >
        <div className={`fmtm-fixed fmtm-left-0`} ref={logoRef}>
          <img src={FmtmLogo} alt="Hot Fmtm Logo" className="fmtm-ml-2 fmtm-z-10 fmtm-w-[5.2rem]  fmtm-mb-4" />
        </div>
        <div
          ref={sheetContentRef}
          className={`bottom-sheet-content fmtm-shadow-[30px_-10px_10px_5px_rgba(0,0,0,0.1)] fmtm-w-full fmtm-relative fmtm-bg-white fmtm-max-h-[100vh] fmtm-h-[50vh] fmtm-max-w-[1150px] fmtm-py-6 fmtm-px-4 fmtm-duration-300 fmtm-ease-in-out fmtm-overflow-hidden ${
            !show ? 'fmtm-translate-y-[100%]' : 'fmtm-translate-y-[0%]'
          } ${isDragging ? 'fmtm-transition-none' : ''} ${isFullScreen ? 'fmtm-rounded-none' : 'fmtm-rounded-t-2xl'}`}
        >
          <div className="header fmtm-flex fmtm-justify-center">
            <div
              className="drag-icon fmtm-cursor-grab fmtm-select-none fmtm-p-4 -fmtm-mt-4 fmtm-z-[9999]"
              onMouseDown={dragStart}
              onTouchStart={dragStart}
              onMouseMove={dragging}
              onTouchMove={dragging}
              onMouseUp={dragStop}
              onTouchEnd={dragStop}
            >
              <span className="fmtm-h-1 fmtm-w-[2.5rem] fmtm-block fmtm-bg-[#c7d0e1] fmtm-rounded-full hover:fmtm-bg-primaryRed"></span>
            </div>
          </div>
          <div className="body fmtm-overflow-y-scroll scrollbar fmtm-h-full fmtm-p-[1px]">{body}</div>
        </div>
      </div>
    </div>
  );
};

export default BottomSheet;
