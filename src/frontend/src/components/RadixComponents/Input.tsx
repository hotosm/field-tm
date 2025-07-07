import * as React from 'react';

import { cn } from '@/utilfunctions/shadcn';

function Input({ className, type, ...props }: React.ComponentProps<'input'>) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        'file:fmtm-text-foreground placeholder:fmtm-text-muted-foreground selection:fmtm-bg-primary selection:fmtm-text-primary-foreground dark:fmtm-bg-input/30 fmtm-border-input fmtm-flex fmtm-h-9 fmtm-w-full fmtm-min-w-0 fmtm-rounded-md fmtm-border fmtm-bg-transparent fmtm-px-3 fmtm-py-1 fmtm-text-base fmtm-shadow-xs fmtm-transition-[color,box-shadow] fmtm-outline-none file:fmtm-inline-flex fmtm-file:fmtm-h-7 file:fmtm-border-0 file:fmtm-bg-transparent file:fmtm-text-sm file:fmtm-font-medium disabled:fmtm-pointer-events-none disabled:fmtm-cursor-not-allowed disabled:fmtm-opacity-50 fmtm-md:fmtm-text-sm',
        'focus-visible:fmtm-border-[#D73F37] focus-visible:fmtm-ring-[#D73F37]/50 focus-visible:fmtm-ring-[3px]',
        'aria-invalid:fmtm-ring-[#D73F37]/20 dark:fmtm-aria-invalid:fmtm-ring-[#B11E20]/40 aria-invalid:fmtm-border-[#D73F37]',
        className,
      )}
      {...props}
    />
  );
}

export { Input };
