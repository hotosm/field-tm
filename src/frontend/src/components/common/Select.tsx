import * as React from 'react';
import * as SelectPrimitive from '@radix-ui/react-select';
import { Check, ChevronDown } from 'lucide-react';

import { cn } from '@/utilfunctions/shadcn';

const Select = SelectPrimitive.Root;

const SelectGroup = SelectPrimitive.Group;

const SelectValue = SelectPrimitive.Value;

const SelectTrigger = ({ className, children, ref, ...props }) => (
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
);
SelectTrigger.displayName = SelectPrimitive.Trigger.displayName;

const SelectContent = ({ className, children, position = 'popper', ref, ...props }) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content
      ref={ref}
      className={cn(
        'fmtm-relative fmtm-z-50 fmtm-min-w-[8rem] fmtm-overflow-hidden fmtm-rounded-md fmtm-border fmtm-bg-white text-popover-foreground fmtm-shadow-md data-[state=open]:fmtm-animate-in data-[state=closed]:fmtm-animate-out data-[state=closed]:fmtm-fade-out-0 data-[state=open]:fmtm-fade-in-0 data-[state=closed]:fmtm-zoom-out-95 data-[state=open]:fmtm-zoom-in-95 data-[side=bottom]:fmtm-slide-in-from-top-2 data-[side=left]:fmtm-slide-in-from-right-2 data-[side=right]:fmtm-slide-in-from-left-2 data-[side=top]:fmtm-slide-in-from-bottom-2',
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
);
SelectContent.displayName = SelectPrimitive.Content.displayName;

const SelectLabel = ({ className, ref, ...props }) => (
  <SelectPrimitive.Label
    ref={ref}
    className={cn('fmtm-py-1.5 fmtm-pl-8 fmtm-pr-2 fmtm-text-[1rem] fmtm-font-semibold', className)}
    {...props}
  />
);
SelectLabel.displayName = SelectPrimitive.Label.displayName;

const SelectItem = ({ className, children, ref, ...props }) => (
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
);
SelectItem.displayName = SelectPrimitive.Item.displayName;

const SelectSeparator = ({ className, ref, ...props }) => (
  <SelectPrimitive.Separator
    ref={ref}
    className={cn('fmtm--mx-1 fmtm-my-1 fmtm-h-px fmtm-bg-gray-500', className)}
    {...props}
  />
);
SelectSeparator.displayName = SelectPrimitive.Separator.displayName;

interface ICustomSelect {
  title: string;
  placeholder: string;
  data: any;
  dataKey: string;
  value?: string;
  valueKey: string;
  label: string;
  onValueChange?: (value: string | null | number) => void;
  errorMsg?: string;
  className?: string;
  required?: boolean;
  disabled?: boolean;
}

export const CustomSelect = ({
  title,
  placeholder,
  data,
  dataKey,
  value,
  valueKey,
  label,
  onValueChange,
  errorMsg,
  className,
  required,
  disabled = false,
}: ICustomSelect) => {
  return (
    <div className="fmtm-w-full">
      {title && (
        <div className="fmtm-flex fmtm-gap-1">
          <p className={`fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold !fmtm-bg-transparent ${className}`}>{title}</p>
          {required && <p className="fmtm-text-red-500 fmtm-text-[1.2rem]">*</p>}
        </div>
      )}
      <div className="fmtm-flex fmtm-items-end">
        <div className={`fmtm-w-full ${className}`}>
          <Select
            disabled={disabled}
            value={value}
            onValueChange={(value) => {
              if (onValueChange) return onValueChange(value);
            }}
          >
            <SelectTrigger className="fmtm-h-[2.35rem]">
              <SelectValue placeholder={placeholder} />
            </SelectTrigger>
            <SelectContent className="fmtm-z-[100]">
              <SelectGroup className="fmtm-max-h-72 fmtm-overflow-y-auto">
                {data?.map((item) => (
                  <SelectItem key={item[dataKey]} value={item[valueKey].toString()}>
                    {item[label]}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
      </div>
      {errorMsg && <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">{errorMsg}</p>}
    </div>
  );
};

export { Select, SelectGroup, SelectValue, SelectTrigger, SelectContent, SelectLabel, SelectItem, SelectSeparator };
