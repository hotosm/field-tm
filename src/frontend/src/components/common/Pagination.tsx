import React, { useState } from 'react';
import AssetModules from '@/shared/AssetModules';
import usePagination, { DOTS } from '@/hooks/usePagination';

type paginationPropType = {
  showing: number;
  totalCount: number;
  currentPage: number;
  pageSize: number;
  handlePageChange: (page: number) => void;
  isLoading: boolean;
  className?: string;
};

export default function Pagination({
  showing,
  totalCount,
  currentPage,
  pageSize,
  handlePageChange,
  isLoading,
  className,
}: paginationPropType) {
  const paginationRange = usePagination({
    currentPage,
    totalCount,
    pageSize,
  });

  const [currentPageState, setCurrentPageState] = useState<number | string>(currentPage);

  return (
    <div
      className={`fmtm-bottom-0 fmtm-flex fmtm-items-center fmtm-justify-between fmtm-flex-col sm:fmtm-flex-row fmtm-bg-white fmtm-py-2 fmtm-px-11 fmtm-shadow-black fmtm-shadow-2xl fmtm-z-50 fmtm-gap-1 ${className}`}
    >
      <p className="fmtm-body-sm fmtm-text-grey-800">
        Showing {showing} of {totalCount} results
      </p>

      <div className="fmtm-flex fmtm-flex-wrap fmtm-justify-center fmtm-gap-x-6 fmtm-gap-y-1">
        {/* Go to page */}
        <div className="fmtm-flex fmtm-flex-1 fmtm-items-center fmtm-justify-center fmtm-gap-2 fmtm-md:pr-6">
          <p className="fmtm-body-sm fmtm-whitespace-nowrap fmtm-text-grey-800">Go to Page</p>
          <input
            type="number"
            min={1}
            disabled={isLoading}
            defaultValue={currentPageState}
            value={currentPageState}
            onChange={(e) => {
              const value =
                Number(e.target.value) > (paginationRange[paginationRange.length - 1] as number)
                  ? (paginationRange[paginationRange.length - 1] as number)
                  : +e.target.value;
              setCurrentPageState(value);
              handlePageChange(value);
            }}
            className="fmtm-body-md fmtm-outline-none fmtm-border fmtm-border-[#D0D5DD] fmtm-rounded-lg fmtm-w-8 fmtm-h-8 fmtm-p-1"
          />
        </div>

        {/* pagination-numbers */}
        {paginationRange.length > 1 && (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-overflow-x-auto fmtm-max-sm:w-[100%] fmtm-max-sm:justify-center">
            {/* previous button */}
            <button
              disabled={currentPage === 1}
              onClick={() => {
                handlePageChange(currentPage - 1);
              }}
              className={`fmtm-w-5 fmtm-h-5 fmtm-min-w-5 fmtm-min-h-5 fmtm-rounded-full fmtm-flex fmtm-items-center fmtm-justify-center ${currentPage === 1 ? 'fmtm-cursor-not-allowed fmtm-text-grey-400' : 'hover:fmtm-bg-red-50 fmtm-duration-100 hover:fmtm-text-red-600'}`}
            >
              <AssetModules.ChevronLeftIcon className="!fmtm-text-sm" />
            </button>

            {/* Page Numbers */}
            {paginationRange.map((pageNumber) => {
              if (pageNumber === DOTS) {
                return (
                  <span key={pageNumber} className="fmtm-body-sm-regular fmtm-text-black-600">
                    &#8230;
                  </span>
                );
              }
              return (
                <div
                  className={`fmtm-grid fmtm-h-8 fmtm-cursor-pointer fmtm-place-items-center fmtm-px-3 fmtm-transition-colors hover:fmtm-text-primary-900 fmtm-border-b ${
                    currentPage === pageNumber ? 'fmtm-border-grey-800' : 'fmtm-border-white'
                  }`}
                  key={pageNumber}
                  onClick={() => {
                    handlePageChange(pageNumber as number);
                  }}
                >
                  <p
                    className={`fmtm-body-sm ${currentPage === pageNumber ? 'fmtm-font-bold fmtm-text-[#212121]' : 'fmtm-texy-grey-800'}`}
                  >
                    {pageNumber}
                  </p>
                </div>
              );
            })}
            {/* next button */}
            <button
              disabled={currentPage === paginationRange[paginationRange.length - 1]}
              onClick={() => {
                handlePageChange(currentPage + 1);
              }}
              className={`fmtm-w-5 fmtm-h-5 fmtm-min-w-5 fmtm-min-h-5 fmtm-rounded-full fmtm-flex fmtm-items-center fmtm-justify-center ${currentPage === paginationRange[paginationRange.length - 1] ? 'fmtm-cursor-not-allowed fmtm-text-grey-400' : 'hover:fmtm-bg-red-50 fmtm-duration-100 hover:fmtm-text-red-600'}`}
            >
              <AssetModules.ChevronRightIcon className="!fmtm-text-sm" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
