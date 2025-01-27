import * as React from 'react';
import * as SelectPrimitive from '@radix-ui/react-select';
import { Check, ChevronDown } from 'lucide-react';

import { cn } from '@/utilfunctions/shadcn';

const Select = SelectPrimitive.Root;

const SelectGroup = SelectPrimitive.Group;

const SelectValue = SelectPrimitive.Value;

const SelectTrigger = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(({ className = '', children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    className={cn(
      `border-input ring-offset-background placeholder:text-muted-foreground focus:ring-ring fmtm-flex fmtm-h-10 fmtm-w-full fmtm-items-center 
       fmtm-justify-between fmtm-rounded-md fmtm-border fmtm-bg-white fmtm-px-3 fmtm-py-2
       fmtm-text-sm focus:fmtm-outline-none focus:fmtm-ring-2 focus:fmtm-ring-offset-2 disabled:fmtm-cursor-not-allowed 
       disabled:fmtm-opacity-50`,
      className,
    )}
    {...props}
  >
    {children}
    <SelectPrimitive.Icon asChild>
      <ChevronDown className="fmtm-h-4 fmtm-w-4 fmtm-opacity-50" />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
));
SelectTrigger.displayName = SelectPrimitive.Trigger.displayName;

const SelectContent = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>
>(({ className, children, position = 'popper', ...props }, ref) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content
      ref={ref}
      className={cn(
        `fmtm-relative fmtm-z-50 fmtm-min-w-[8rem] fmtm-overflow-hidden fmtm-text-grey-800 fmtm-shadow-md fmtm-animate-in fmtm-fade-in-80`,
        position === 'popper' && 'translate-y-1',
        className,
      )}
      position={position}
      {...props}
    >
      <SelectPrimitive.Viewport
        className={cn(
          'fmtm-p-1',
          position === 'popper' &&
            'fmtm-h-[var(--radix-select-trigger-height)] fmtm-w-full fmtm-min-w-[var(--radix-select-trigger-width)]',
        )}
      >
        {children}
      </SelectPrimitive.Viewport>
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
));
SelectContent.displayName = SelectPrimitive.Content.displayName;

const SelectLabel = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Label>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Label
    ref={ref}
    className={cn('fmtm-py-1.5 fmtm-pl-8 fmtm-pr-2 fmtm-text-sm fmtm-font-semibold', className)}
    {...props}
  />
));
SelectLabel.displayName = SelectPrimitive.Label.displayName;

const SelectItem = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Item
    ref={ref}
    className={cn(
      'focus:fmtm-bg-primarycolor focus:text-accent-foreground fmtm-relative fmtm-flex fmtm-w-full fmtm-cursor-default fmtm-select-none fmtm-items-center fmtm-rounded-sm fmtm-py-1.5 fmtm-pl-8 fmtm-pr-2 fmtm-text-sm fmtm-outline-none data-[disabled]:fmtm-pointer-events-none data-[disabled]:fmtm-opacity-50',
    )}
    {...props}
  >
    <span className="fmtm-absolute fmtm-left-2 fmtm-flex fmtm-h-3.5 fmtm-w-3.5 fmtm-items-center fmtm-justify-center">
      <SelectPrimitive.ItemIndicator>
        <Check className="fmtm-h-4 fmtm-w-4" />
      </SelectPrimitive.ItemIndicator>
    </span>

    <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
));
SelectItem.displayName = SelectPrimitive.Item.displayName;

const SelectSeparator = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Separator
    ref={ref}
    className={cn('fmtm-bg-muted fmtm--mx-1 fmtm-my-1 fmtm-h-px', className)}
    {...props}
  />
));
SelectSeparator.displayName = SelectPrimitive.Separator.displayName;

export { Select, SelectGroup, SelectValue, SelectTrigger, SelectContent, SelectLabel, SelectItem, SelectSeparator };
