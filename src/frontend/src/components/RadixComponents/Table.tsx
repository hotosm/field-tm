import * as React from 'react';

import { cn } from '@/utilfunctions/shadcn';

const Table = React.forwardRef<HTMLTableElement, React.HTMLAttributes<HTMLTableElement>>(
  ({ className, ...props }, ref) => (
    <div className="fmtm-table-wrapper">
      <table
        ref={ref}
        className={cn('fmtm-table-container fmtm-relative fmtm-w-full fmtm-overflow-y-auto fmtm-rounded-lg', className)}
        {...props}
      />
    </div>
  ),
);
Table.displayName = 'Table';

const TableHeader = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ className, ...props }, ref) => (
    <thead
      ref={ref}
      className={cn(
        'fmtm-table-header fmtm-sticky fmtm-top-0 fmtm-z-10 fmtm-border-b-[#EAECF0] fmtm-bg-grey-200 [&_tr]:fmtm-border-b',
        className,
      )}
      {...props}
    />
  ),
);
TableHeader.displayName = 'TableHeader';

const TableBody = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ className, ...props }, ref) => (
    <tbody
      ref={ref}
      className={cn('fmtm-table-body fmtm-bg-white [&_tr:last-child]:fmtm-border-0', className)}
      {...props}
    />
  ),
);
TableBody.displayName = 'TableBody';

const TableRow = React.forwardRef<HTMLTableRowElement, React.HTMLAttributes<HTMLTableRowElement>>(
  ({ className, ...props }, ref) => (
    <tr
      ref={ref}
      className={cn(
        'data-[state=selected]:-fmtm-bg-muted fmtm-table-body-row fmtm-border-b fmtm-border-b-black-200',
        className,
      )}
      {...props}
    />
  ),
);
TableRow.displayName = 'TableRow';

const TableHead = React.forwardRef<HTMLTableCellElement, React.ThHTMLAttributes<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <th
      ref={ref}
      className={cn(
        'fmtm-whitespace-nowrap fmtm-p-3 fmtm-text-neutral-gray [&:not(:first-child):not(:last-child)]:fmtm-border-x-[1px] fmtm-border-white fmtm-text-grey-800 [&:has([role=checkbox])]:fmtm-pr-0 ',
        className,
      )}
      {...props}
    />
  ),
);
TableHead.displayName = 'TableHead';

const TableCell = React.forwardRef<HTMLTableCellElement, React.TdHTMLAttributes<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <td
      ref={ref}
      className={cn(
        'fmtm-table-body-column fmtm-table-body fmtm-h-11 fmtm-px-3 fmtm-text-grey-800 fmtm-text-[15px] [&:has([role=checkbox])]:fmtm-pr-0',
        className,
      )}
      {...props}
    />
  ),
);
TableCell.displayName = 'TableCell';

const TableFooter = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ className, ...props }, ref) => (
    <tfoot
      ref={ref}
      className={cn('fmtm-text-primary-foreground fmtm-bg-primary-600 fmtm-font-medium', className)}
      {...props}
    />
  ),
);
TableFooter.displayName = 'TableFooter';

const TableCaption = React.forwardRef<HTMLTableCaptionElement, React.HTMLAttributes<HTMLTableCaptionElement>>(
  ({ className, ...props }, ref) => <caption ref={ref} className={cn('fmtm-mt-4', className)} {...props} />,
);
TableCaption.displayName = 'TableCaption';

export { Table, TableHeader, TableBody, TableFooter, TableHead, TableRow, TableCell, TableCaption };
