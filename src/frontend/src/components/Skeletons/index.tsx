import React from 'react';
import { cn } from '@/utilfunctions/shadcn';

export const Skeleton = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => {
  return <div className={cn('fmtm-animate-pulse fmtm-rounded-md fmtm-bg-grey-300', className)} {...props} />;
};
