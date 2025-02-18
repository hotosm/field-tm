import React, { useEffect, useRef, useState } from 'react';
import AssetModules from '@/shared/AssetModules';
import { Dialog, DialogContent } from '@/components/common/Modal';

type ImageSliderProps = {
  // key:value pairs of {filename:URL}
  images: Record<string, string>;
};

const ImageSlider = ({ images }: ImageSliderProps) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const [isOverflowing, setIsOverflowing] = useState(false);
  const [showRightButton, setShowRightButton] = useState(false);
  const [showLeftButton, setShowLeftButton] = useState(false);
  const [selectedImageURL, setSelectedImageURL] = useState<string | null>(null);
  const [translateImage, setTranslateImage] = useState(0);

  useEffect(() => {
    if (scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      setIsOverflowing(container.scrollWidth > container.clientWidth);
      handleScroll();
    }
  }, [images]);

  const handleScroll = () => {
    if (scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      const atStart = container.scrollLeft === 0;
      const atEnd = container.scrollLeft + container.clientWidth >= container.scrollWidth - 1;
      setShowLeftButton(!atStart);
      setShowRightButton(!atEnd);
    }
  };

  return (
    <>
      {/* Fullscreen Image Viewer */}
      <Dialog
        open={selectedImageURL ? true : false}
        onOpenChange={(status) => {
          if (!status) {
            setSelectedImageURL(null);
            setTranslateImage(0);
          }
        }}
      >
        <DialogContent className="!fmtm-bg-transparent fmtm-border-none fmtm-shadow-none fmtm-h-[100vh] fmtm-w-[100vw]">
          <div className="fmtm-z-50 fmtm-relative fmtm-overflow-hidden fmtm-p-4 fmtm-w-full fmtm-flex fmtm-justify-center">
            <img
              src={selectedImageURL || ''}
              alt="submission"
              className="fmtm-max-w-[95%] fmtm-max-h-[80vh] fmtm-object-cover"
              style={{
                transform: `rotate(${translateImage}deg)`,
              }}
            />
          </div>
          <div className="fmtm-flex fmtm-items-center fmtm-gap-4 fmtm-px-4 fmtm-py-2 fmtm-absolute fmtm-bottom-5 fmtm-w-fit fmtm-bg-black fmtm-bg-opacity-30 fmtm-rounded-md fmtm-z-50 fmtm-left-[50%] fmtm-translate-x-[-50%]">
            <AssetModules.RotateLeftIcon
              className="fmtm-text-white fmtm-cursor-pointer hover:fmtm-scale-110 fmtm-duration-150"
              onClick={() => setTranslateImage(translateImage - 90)}
            />
            <AssetModules.RotateRightIcon
              className="fmtm-text-white fmtm-cursor-pointer hover:fmtm-scale-110 fmtm-duration-150"
              onClick={() => setTranslateImage(translateImage + 90)}
            />
          </div>
        </DialogContent>
      </Dialog>

      {/* Image Slider */}
      <div
        className="fmtm-flex fmtm-gap-x-3 fmtm-w-full fmtm-overflow-x-scroll scrollbar fmtm-relative"
        ref={scrollContainerRef}
        onScroll={handleScroll}
      >
        {/* Left Scroll Button */}
        {showLeftButton && (
          <button
            className={`fmtm-sticky fmtm-left-2 fmtm-my-auto fmtm-z-50 fmtm-w-fit fmtm-p-1 fmtm-rounded-full fmtm-bg-black fmtm-bg-opacity-50 fmtm-h-fit hover:fmtm-scale-110 fmtm-cursor-pointer fmtm-duration-300`}
            onClick={() => {
              scrollContainerRef?.current?.scrollBy({ left: -300, behavior: 'smooth' });
            }}
          >
            <AssetModules.ChevronLeftIcon className="fmtm-text-white" />
          </button>
        )}

        {/* Image List */}
        {Object.entries(images).map(([filename, imageUrl]) => (
          <div
            key={filename}
            onClick={() => setSelectedImageURL(imageUrl)}
            className="fmtm-h-[10.313rem] fmtm-w-[9.688rem] fmtm-min-w-[9.688rem] fmtm-rounded-lg fmtm-overflow-hidden fmtm-cursor-pointer"
          >
            <img src={imageUrl} alt="submission image" className="fmtm-h-full fmtm-w-full fmtm-object-cover" />
          </div>
        ))}

        {/* Right Scroll Button */}
        {((isOverflowing && showRightButton) || (isOverflowing && scrollContainerRef?.current?.scrollLeft === 0)) && (
          <button
            className={`fmtm-sticky fmtm-right-2 fmtm-my-auto fmtm-z-50 fmtm-w-fit fmtm-p-1 fmtm-rounded-full fmtm-bg-black fmtm-bg-opacity-50 fmtm-h-fit hover:fmtm-scale-110 fmtm-cursor-pointer fmtm-duration-300`}
            onClick={() => {
              scrollContainerRef?.current?.scrollBy({ left: 300, behavior: 'smooth' });
            }}
          >
            <AssetModules.ChevronRightIcon className="fmtm-text-white" />
          </button>
        )}
      </div>
    </>
  );
};

export default ImageSlider;
