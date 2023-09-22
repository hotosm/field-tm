import * as React from 'react';
import * as SelectPrimitive from '@radix-ui/react-select';
import { Check, ChevronDown } from 'lucide-react';

import { cn } from '../../utilfunctions/shadcn';

const Select = SelectPrimitive.Root;

const SelectGroup = SelectPrimitive.Group;

const SelectValue = SelectPrimitive.Value;

const SelectTrigger = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    className={cn(
      'fmtm-flex fmtm-h-[2rem] fmtm-w-full fmtm-items-center fmtm-justify-between fmtm-border fmtm-border-gray-300 fmtm-bg-background fmtm-px-3 fmtm-py-2 fmtm-text-[1rem] placeholder:fmtm-text-black focus:fmtm-outline-none disabled:fmtm-cursor-not-allowed disabled:fmtm-opacity-50',
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
        'fmtm-relative fmtm-z-50 fmtm-min-w-[8rem] fmtm-overflow-hidden fmtm-rounded-md fmtm-border fmtm-bg-white text-popover-foreground fmtm-shadow-md data-[state=open]:fmtm-animate-in data-[state=closed]:fmtm-animate-out data-[state=closed]:fmtm-fade-out-0 data-[state=open]:fmtm-fade-in-0 data-[state=closed]:fmtm-zoom-out-95 fmtm-data-[state=open]:zoom-in-95 data-[side=bottom]:fmtm-slide-in-from-top-2 data-[side=left]:fmtm-slide-in-from-right-2 data-[side=right]:fmtm-slide-in-from-left-2 data-[side=top]:fmtm-slide-in-from-bottom-2',
        position === 'popper' &&
          'data-[side=bottom]:fmtm-translate-y-1 data-[side=left]:fmtm--translate-x-1 data-[side=right]:fmtm-translate-x-1 data-[side=top]:fmtm--translate-y-1',
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
    className={cn('fmtm-py-1.5 fmtm-pl-8 fmtm-pr-2 fmtm-text-[1rem] fmtm-font-semibold', className)}
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
      'fmtm-relative fmtm-flex fmtm-w-full fmtm-cursor-default fmtm-select-none fmtm-items-center fmtm-rounded-sm fmtm-py-1.5 fmtm-pl-8 fmtm-pr-2 fmtm-text-[1rem] fmtm-outline-none focus:fmtm-bg-gray-100  data-[disabled]:fmtm-pointer-events-none data-[disabled]:fmtm-opacity-50',
      className,
    )}
    {...props}
  >
    <span className="fmtm-absolute fmtm-left-2 fmtm-flex fmtm-h-3.5 fmtm-w-3.5 fmtm-items-center fmtm-justify-center">
      <SelectPrimitive.ItemIndicator>
        <Check className="fmtm-h-4 fmtm-w-4 fmtm-text-red-600 fmtm-font-bold" />
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
    className={cn('fmtm--mx-1 fmtm-my-1 fmtm-h-px fmtm-bg-gray-500', className)}
    {...props}
  />
));
SelectSeparator.displayName = SelectPrimitive.Separator.displayName;

export { Select, SelectGroup, SelectValue, SelectTrigger, SelectContent, SelectLabel, SelectItem, SelectSeparator };
