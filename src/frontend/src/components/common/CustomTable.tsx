/* eslint-disable react/no-unknown-property */
/* eslint-disable react/self-closing-comp */
/* eslint-disable react/no-array-index-key */
/* eslint-disable react/no-unstable-nested-components */
/* eslint-disable no-unused-vars */
/* eslint-disable react/jsx-props-no-spreading */
import React, { Component, Children, ReactNode, CSSProperties } from 'react';
import CoreModules from '../../shared/CoreModules';
import { milliseconds } from 'date-fns';

type TableHeaderType = {
  dataField: string;
  dataFormat?: (row: any, cell: any, index: number) => ReactNode;
  isSubHeader?: boolean;
  dataHeader?: string;
  rowcolSpan?: string;
  headerClassName?: string;
  containSubHeader?: boolean;
  rowClassName: string;
};

export function TableHeader({
  dataField = '',
  dataFormat = null,
  isSubHeader = false,
  dataHeader = null,
  rowcolSpan = '',
  headerClassName = '',
  containSubHeader = false,
}: TableHeaderType) {
  return (
    <div
      dataField={dataField}
      dataFormat={dataFormat}
      dataHeader={dataHeader}
      isSubHeader={isSubHeader}
      containSubHeader={containSubHeader}
      rowcolSpan={rowcolSpan}
      headerClassName={headerClassName}
    />
  );
}

type TableProps = {
  uniqueKey: string;
  data: any[];
  children?: ReactNode;
  showHeader?: boolean;
  onRowClick?: (row: any) => void;
  className?: string;
  tableClassName?: string;
  style?: CSSProperties;
  headerWidths?: string[];
  loadMoreRef?: React.RefObject<HTMLDivElement>;
  parentloadMoreRef?: React.RefObject<HTMLDivElement>;
  rowColSpanNum?: string[];
  rowcolSpanName?: string[];
  headClassName?: string[];
  trClassName?: string;
  scrollElement?: ReactNode;
  flag?: string;
  isLoading?: boolean;
};

export default class Table extends Component<TableProps> {
  static defaultProps: Partial<TableProps> = {
    uniqueKey: '',
    children: null,
    showHeader: true,
    onRowClick: null,
    className: '',
    tableClassName: '',
    style: {},
    headerWidths: [],
    loadMoreRef: null,
    parentloadMoreRef: null,
    rowColSpanNum: [],
    rowcolSpanName: [],
    headClassName: [],
    trClassName: '',
    scrollElement: null,
    flag: '',
    isLoading: false,
  };

  getFields = () => {
    const { data, children } = this.props;
    const numberOfChildren = Children.count(children);
    if (numberOfChildren > 0) {
      const isSubheaderCollection = Children.map(children, (child: any) => child?.props?.isSubHeader);
      const containSubHeaderCollection = Children.map(children, (child: any) => child?.props?.containSubHeader);
      const fields = Children.map(children, (child: any) => child?.props?.dataField);
      const rowColSpanValue = Children.map(children, (child: any) => child?.props?.rowcolSpan);
      const headClassName = Children.map(children, (child: any) => child?.props?.headerClassName);
      const rowClassName = Children.map(children, (child: any) => child?.props?.rowClassName);
      return {
        fields,
        rowColSpanValue,
        headClassName,
        isSubheaderCollection,
        containSubHeaderCollection,
        rowClassName,
      };
    }
    return data.length > 0 ? Object.keys(data[0]) : [];
  };

  getHeaderData = (field: string) => {
    const { children } = this.props;
    const numberOfChildren = Children.count(children);
    if (numberOfChildren > 0) {
      const tableChildren = Children.toArray(children) as React.ReactElement[];
      const tableChildWithSameFieldAndDataHeader = tableChildren.find(
        (child) => child.props.dataField === field && child.props.dataHeader !== null,
      );

      if (tableChildWithSameFieldAndDataHeader) {
        return tableChildWithSameFieldAndDataHeader.props.dataField;
      }

      return field;
    }

    if (typeof field === 'object') return null;

    return field;
  };

  getBodyCellData = (row: any, field: string, index: number) => {
    const { children } = this.props;
    const numberOfChildren = Children.count(children);
    if (numberOfChildren > 0) {
      const tableChildren = Children.toArray(children) as React.ReactElement[];
      const tableChildWithSameFieldAndDataFormat = tableChildren.find(
        (child) => child.props.dataField === field && child.props.dataFormat !== null,
      );

      if (tableChildWithSameFieldAndDataFormat) {
        return tableChildWithSameFieldAndDataFormat.props.dataFormat(row, row[field], index);
      }

      return row[field];
    }

    if (typeof row[field] === 'object') return null;

    return row[field];
  };

  renderHeader = () => {
    const { fields, rowColSpanValue, headClassName, isSubheaderCollection } = this.getFields();
    const { headerWidths, data, flag } = this.props;
    return fields.map((field, index) => {
      const isSubHeader = isSubheaderCollection[index];
      const rowCol = rowColSpanValue[index]?.split('_');
      return (
        <th
          key={field}
          {...(rowCol && { [rowCol[0]]: rowCol[1] })}
          {...(headClassName[index] && { className: headClassName[index] })}
          {...(headerWidths &&
            headerWidths[index] &&
            data.length > 0 && {
              style: {
                width: headerWidths[index],
                minWidth: headerWidths[index],
                maxWidth: headerWidths[index],
              },
            })}
          className={`${
            headClassName[index]
          } fmtm-px-5 fmtm-pt-4 fmtm-pb-4 fmtm-bg-black-100 fmtm-align-middle fmtm-text-body-sm fmtm-leading-5 fmtm-text-left fmtm-capitalize fmtm-font-bold fmtm-border-[1px] fmtm-text-sm fmtm-max-w-[11rem] ${
            flag?.toLowerCase() === 'primarytable'
              ? 'fmtm-bg-primaryRed fmtm-text-white fmtm-border-white'
              : 'fmtm-bg-[#F0F0F0] fmtm-border-[#B9B9B9]'
          }`}
        >
          {this.getHeaderData(field)}
        </th>
      );
    });
  };

  renderSubHeader = () => {
    const { fields, headClassName, isSubheaderCollection } = this.getFields();
    const { headerWidths, data } = this.props;
    return fields.map((field, index) => {
      const isSubHeader = isSubheaderCollection[index];
      return (
        isSubHeader && (
          <th
            key={field}
            {...{ className: headClassName[index] }}
            {...(headerWidths[index] && data.length > 0 && { style: { width: headerWidths[index] } })}
            className="fmtm-align-middle fmtm-text-body-sm fmtm-leading-4 fmtm-text-left fmtm-capitalize fmtm-font-bold fmtm-border-[1px] fmtm-border-[#B9B9B9]"
          >
            {this.getHeaderData(field)}
          </th>
        )
      );
    });
  };

  renderRow = () => {
    const { data, uniqueKey, onRowClick, trClassName, flag, isLoading } = this.props;
    const { fields, containSubHeaderCollection, rowClassName } = this.getFields();
    if (isLoading === false && fields.length > 0 && data.length === 0) {
      return (
        <tr>
          <td colSpan={fields.length} className="fmtm-text-center fmtm-py-4 fmtm-text-gray-500">
            No data available.
          </td>
        </tr>
      );
    }
    if (isLoading) {
      return Array.from({ length: 5 }).map((_, i) => (
        <tr
          key={i}
          className={` ${
            flag?.toLowerCase() === 'dashboard' ? '' : 'hover:fmtm-bg-active_bg'
          } fmtm-cursor-pointer fmtm-ease-in fmtm-duration-100 fmtm-h-[50px] 
      fmtm-items-baseline fmtm-relative fmtm-bg-white`}
        >
          {fields.map(
            (field, ind) =>
              !containSubHeaderCollection[ind] && (
                <td
                  key={ind}
                  className={`${rowClassName[ind]} fmtm-text-slate-900 fmtm-font-normal fmtm-text-body-md fmtm-px-5 fmtm-relative fmtm-border-[1px] fmtm-border-[#B9B9B9]`}
                >
                  <CoreModules.Skeleton className="!fmtm-w-full" />
                </td>
              ),
          )}
        </tr>
      ));
    } else {
      return data?.map((row, index) => (
        <tr
          key={`tr_${row[uniqueKey] || index}`}
          {...(onRowClick && {
            onClick: () => onRowClick(row),
            style: { cursor: 'pointer' },
          })}
          className={`${trClassName && trClassName(row)} ${
            flag?.toLowerCase() === 'primarytable'
              ? `${(index + 1) % 2 === 0 ? '!fmtm-bg-[#F3F3F3]' : 'fmtm-bg-white'}`
              : ''
          } fmtm-cursor-pointer fmtm-ease-in fmtm-duration-100 fmtm-h-[50px]
          fmtm-items-baseline fmtm-relative fmtm-bg-white`}
        >
          {fields.map(
            (field, ind) =>
              !containSubHeaderCollection[ind] && (
                <td
                  key={`${field}_${row[field] || ind}_${row[uniqueKey] || ind}`.replace(/ /g, '_')}
                  className={`${
                    rowClassName[ind]
                  } fmtm-text-slate-900 fmtm-font-normal fmtm-text-body-md fmtm-px-5 fmtm-relative ${
                    flag?.toLowerCase() === 'primarytable' ? '' : 'fmtm-border-[1px] fmtm-border-[#B9B9B9]'
                  }`}
                >
                  {this.getBodyCellData(row, field, index)}
                </td>
              ),
          )}
        </tr>
      ));
    }
  };

  render() {
    const { showHeader, className, style, tableClassName, loadMoreRef, parentloadMoreRef, scrollElement, flag } =
      this.props;
    return (
      <div
        ref={parentloadMoreRef}
        className={`fmtm-block fmtm-pb-1 fmtm-overflow-x-auto fmtm-mt-3 scrollbar ${tableClassName}`}
        style={style}
      >
        <table
          className={`fmtm-w-full fmtm-border-separate fmtm-border-spacing-y-0 ${className} ${
            flag?.toLowerCase() === 'primarytable' ? '' : 'fmtm-border-[1px] fmtm-border-[#B9B9B9]'
          }`}
        >
          {showHeader && (
            <thead className="fmtm-sticky fmtm-top-0 fmtm-z-[2] fmtm-bg-white fmtm-border-b-regular fmtm-border-[#B9B9B9]">
              <tr>{this.renderHeader()}</tr>
              <tr>{this.renderSubHeader()}</tr>
            </thead>
          )}
          <tbody>{this.renderRow()}</tbody>
          <div ref={loadMoreRef} style={{ height: '15px', width: '15px', marginTop: '-1rem' }} />
        </table>
        {scrollElement}
      </div>
    );
  }
}
