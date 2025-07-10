import * as React from 'react';

import { cn } from '@/utilfunctions/shadcn';

function Textarea({ className, ...props }: React.ComponentProps<'textarea'>) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        'fmtm-border-input placeholder:fmtm-text-muted-foreground focus-visible:fmtm-border-[#D73F37] focus-visible:fmtm-ring-[#D73F37]/50 aria-invalid:fmtm-ring-[#D73F37]/20 dark:fmtm-aria-invalid:fmtm-ring-[#B11E20]/40 aria-invalid:fmtm-border-[#D73F37] dark:fmtm-bg-input/30 fmtm-flex field-sizing-content fmtm-min-h-16 fmtm-w-full fmtm-rounded-md fmtm-border fmtm-bg-transparent fmtm-px-3 fmtm-py-2 fmtm-text-base fmtm-shadow-xs transition-[color,box-shadow] fmtm-outline-none focus-visible:fmtm-ring-[3px] disabled:fmtm-cursor-not-allowed disabled:fmtm-opacity-50 md:fmtm-text-sm',
        className,
      )}
      {...props}
    />
  );
}

export { Textarea };
