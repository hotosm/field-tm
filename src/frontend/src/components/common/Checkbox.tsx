'use client';

import * as React from 'react';
import * as CheckboxPrimitive from '@radix-ui/react-checkbox';
import { Check } from 'lucide-react';
import { cn } from '@/utilfunctions/shadcn';

type CustomCheckboxType = {
  label: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  className?: string;
};

const Checkbox = React.forwardRef<
  React.ElementRef<typeof CheckboxPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof CheckboxPrimitive.Root>
>(({ className, ...props }, ref) => (
  <CheckboxPrimitive.Root
    ref={ref}
    className={cn(
      'fmtm-peer fmtm-h-4 fmtm-w-4 fmtm-shrink-0 fmtm-rounded-sm fmtm-border fmtm-border-[#7A7676] fmtm-shadow focus-visible:fmtm-outline-none focus-visible:fmtm-ring-1 disabled:fmtm-cursor-not-allowed disabled:fmtm-opacity-50  data-[state=checked]:fmtm-text-primary-[#7A7676]',
      className,
    )}
    {...props}
  >
    <CheckboxPrimitive.Indicator className={cn('fmtm-flex fmtm-items-center fmtm-justify-center fmtm-text-current')}>
      <Check className="fmtm-h-4 fmtm-w-4 fmtm-text-primaryRed" strokeWidth={4} />
    </CheckboxPrimitive.Indicator>
  </CheckboxPrimitive.Root>
));
Checkbox.displayName = CheckboxPrimitive.Root.displayName;

export const CustomCheckbox = ({ label, checked, onCheckedChange, className }: CustomCheckboxType) => {
  return (
    <div className="fmtm-flex fmtm-gap-2 sm:fmtm-gap-4">
      <Checkbox checked={checked} onCheckedChange={onCheckedChange} className="fmtm-mt-[2px]" />
      <p
        style={{ width: 'calc(100% - 32px)' }}
        className={`fmtm-text-[#7A7676] fmtm-font-archivo fmtm-text-base fmtm-break-words ${className}`}
      >
        {label}
      </p>
    </div>
  );
};
