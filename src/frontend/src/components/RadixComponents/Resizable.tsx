'use client';

import React from 'react';
import { GripVertical } from 'lucide-react';
import * as ResizablePrimitive from 'react-resizable-panels';

import { cn } from '@/utilfunctions/shadcn';

const ResizablePanelGroup = ({ className, ...props }: React.ComponentProps<typeof ResizablePrimitive.PanelGroup>) => (
  <ResizablePrimitive.PanelGroup
    className={cn('flex h-full w-full data-[panel-group-direction=vertical]:flex-col', className)}
    {...props}
  />
);

const ResizablePanel = ResizablePrimitive.Panel;

const ResizableHandle = ({
  withHandle,
  className,
  ...props
}: React.ComponentProps<typeof ResizablePrimitive.PanelResizeHandle> & {
  withHandle?: boolean;
}) => (
  <ResizablePrimitive.PanelResizeHandle
    className={cn(
      'fmtm-relative fmtm-flex fmtm-w-px fmtm-items-center fmtm-justify-center fmtm-bg-border fmtm-after:absolute fmtm-after:inset-y-0 fmtm-after:left-1/2 fmtm-after:w-1 fmtm-after:-translate-x-1/2 fmtm-focus-visible:outline-none fmtm-focus-visible:ring-1 fmtm-focus-visible:ring-ring fmtm-focus-visible:ring-offset-1 data-[panel-group-direction=vertical]:fmtm-h-px data-[panel-group-direction=vertical]:fmtm-w-full data-[panel-group-direction=vertical]:fmtm-after:left-0 data-[panel-group-direction=vertical]:fmtm-after:fmtm-h-1 data-[panel-group-direction=vertical]:fmtm-after:fmtm-w-full data-[panel-group-direction=vertical]:fmtm-after:-translate-y-1/2 data-[panel-group-direction=vertical]:fmtm-after:fmtm-translate-x-0 fmtm-[&[data-panel-group-direction=vertical]>div]:fmtm-rotate-90',
      className,
    )}
    {...props}
  >
    {withHandle && (
      <div className="fmtm-z-10 fmtm-flex fmtm-h-7 fmtm-w-5 fmtm-items-center fmtm-justify-center fmtm-rounded fmtm-border fmtm-bg-border fmtm-bg-gray-50 fmtm-border-none fmtm-shadow-md">
        <GripVertical className="fmtm-h-7 fmtm-w-5 fmtm-text-blue-dark" />
      </div>
    )}
  </ResizablePrimitive.PanelResizeHandle>
);

export { ResizablePanelGroup, ResizablePanel, ResizableHandle };
