import React from 'react';
import { useState } from 'react';
import type { Table } from '@tanstack/react-table';
import clsx from 'clsx';
import AssetModules from '@/shared/AssetModules';
import { ColumnData } from '..';
import usePagination, { DOTS } from '@/hooks/usePagination';

interface IPaginationProps {
  totalCount: number;
  siblingCount?: number;
  currentPage: number;
  pageSize: number;
  isLoading: boolean;
  table: Table<ColumnData>;
  className?: string;
}

export default function DataTablePagination({
  totalCount,
  siblingCount = 1,
  currentPage,
  pageSize,
  isLoading,
  table,
  className,
}: IPaginationProps) {
  const [currentPageState, setCurrentPageState] = useState<number | string>(currentPage);

  const paginationRange = usePagination({
    currentPage,
    totalCount,
    siblingCount,
    pageSize,
  });
  return (
    <div
      className={clsx(
        'fmtm-bottom-0 fmtm-flex fmtm-items-center fmtm-justify-between fmtm-flex-col sm:fmtm-flex-row fmtm-bg-white fmtm-p-2 sm:fmtm-p-3 fmtm-shadow-black fmtm-shadow-2xl fmtm-z-50 fmtm-gap-1',
        className,
      )}
    >
      <p className="fmtm-body-sm fmtm-text-grey-800">
        Showing {table.getRowCount()} of {totalCount} results
      </p>

      <div className="fmtm-flex fmtm-gap-6">
        {/* Go to page */}
        <div className="fmtm-flex fmtm-flex-1 fmtm-items-center fmtm-justify-end fmtm-gap-2 fmtm-md:pr-6">
          <p className=" fmtm-whitespace-nowrap fmtm-body-sm fmtm-text-grey-800">Go to Page</p>
          <input
            type="number"
            min={1}
            disabled={isLoading}
            defaultValue={currentPageState}
            value={currentPageState}
            onChange={(e) => {
              const page = e.target.value ? Number(e.target.value) - 1 : 0;
              const lastPage = table.getPageCount();
              setCurrentPageState(Number(e.target.value) > lastPage ? lastPage : e.target.value);
              table.setPageIndex(page);
            }}
            className="fmtm-body-md fmtm-outline-none fmtm-border fmtm-border-[#D0D5DD] fmtm-rounded-lg fmtm-w-8 fmtm-h-8 fmtm-p-1 fmtm-text-grey-500"
          />
        </div>

        {/* pagination-numbers */}
        {paginationRange.length > 1 && (
          <div className="fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-overflow-x-auto fmtm-max-sm:w-[100%] fmtm-max-sm:justify-center">
            {/* previous button */}
            <button
              disabled={!table.getCanPreviousPage()}
              onClick={() => {
                setCurrentPageState((prev) => Number(prev) - 1);
                table.previousPage();
              }}
              className={`fmtm-w-5 fmtm-h-5 fmtm-min-w-5 fmtm-min-h-5 fmtm-rounded-full fmtm-flex fmtm-items-center fmtm-justify-center ${!table.getCanPreviousPage() ? 'fmtm-cursor-not-allowed fmtm-text-grey-400' : 'hover:fmtm-bg-red-50 fmtm-duration-100 hover:fmtm-text-red-600'}`}
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
                  className={`fmtm-grid fmtm-h-8 fmtm-cursor-pointer fmtm-place-items-center fmtm-px-3 600 fmtm-transition-colors fmtm-border-b ${
                    currentPage === pageNumber ? 'fmtm-border-[#989898]' : 'fmtm-border-white'
                  }`}
                  key={pageNumber}
                  onClick={() => {
                    setCurrentPageState(pageNumber);
                    table.setPageIndex(+pageNumber - 1);
                  }}
                >
                  <p
                    className={`fmtm-body-sm ${currentPage === pageNumber ? 'fmtm-font-bold fmtm-text-[#212121]' : 'fmtm-text-grey-800 hover:fmtm-text-primary-900 fmtm-duration-200'}`}
                  >
                    {pageNumber}
                  </p>
                </div>
              );
            })}
            {/* next button */}
            <button
              disabled={!table.getCanNextPage()}
              onClick={() => {
                setCurrentPageState((prev) => Number(prev) + 1);
                table.nextPage();
              }}
              className={`fmtm-w-5 fmtm-h-5 fmtm-min-w-5 fmtm-min-h-5 fmtm-rounded-full fmtm-flex fmtm-items-center fmtm-justify-center ${!table.getCanNextPage() ? 'fmtm-cursor-not-allowed fmtm-text-grey-400' : 'hover:fmtm-bg-red-50 fmtm-duration-100 hover:fmtm-text-red-600'}`}
            >
              <AssetModules.ChevronRightIcon className="!fmtm-text-sm" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
