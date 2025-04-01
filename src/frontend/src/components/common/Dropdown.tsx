import * as React from 'react';
import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu';
import { CheckIcon, ChevronRightIcon, DotFilledIcon } from '@radix-ui/react-icons';

import { cn } from '@/utilfunctions/shadcn';

const DropdownMenu = DropdownMenuPrimitive.Root;
const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;
const DropdownMenuGroup = DropdownMenuPrimitive.Group;
const DropdownMenuPortal = DropdownMenuPrimitive.Portal;
const DropdownMenuSub = DropdownMenuPrimitive.Sub;
const DropdownMenuRadioGroup = DropdownMenuPrimitive.RadioGroup;

const DropdownMenuSubTrigger = ({ className, inset, children, ref, ...props }) => (
  <DropdownMenuPrimitive.SubTrigger
    ref={ref}
    className={cn(
      'fmtm-flex fmtm-cursor-default fmtm-select-none fmtm-items-center fmtm-rounded-sm fmtm-px-2 fmtm-py-1.5 fmtm-text-sm fmtm-outline-none fmtm-focus:bg-accent data-[state=open]:fmtm-bg-accent',
      inset && 'fmtm-pl-8',
      className,
    )}
    {...props}
  >
    {children}
    <ChevronRightIcon className="ml-auto h-4 w-4" />
  </DropdownMenuPrimitive.SubTrigger>
);
DropdownMenuSubTrigger.displayName = DropdownMenuPrimitive.SubTrigger.displayName;

const DropdownMenuSubContent = ({ className, ref, ...props }) => (
  <DropdownMenuPrimitive.SubContent
    ref={ref}
    className={cn(
      'fmtm-z-50 fmtm-min-w-[8rem] fmtm-overflow-hidden fmtm-rounded-md fmtm-border fmtm-bg-popover fmtm-p-1 fmtm-text-popover-foreground fmtm-shadow-lg data-[state=open]:fmtm-animate-in data-[state=closed]:fmtm-animate-out data-[state=closed]:fmtm-fade-out-0 data-[state=open]:fmtm-fade-in-0 data-[state=closed]:fmtm-zoom-out-95 data-[state=open]:fmtm-zoom-in-95 data-[side=bottom]:fmtm-slide-in-from-top-2 data-[side=left]:fmtm-slide-in-from-right-2 data-[side=right]:fmtm-slide-in-from-left-2 data-[side=top]:fmtm-slide-in-from-bottom-2',
      className,
    )}
    {...props}
  />
);
DropdownMenuSubContent.displayName = DropdownMenuPrimitive.SubContent.displayName;

const DropdownMenuContent = ({ className, sideOffset = 4, ...props }) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.Content
      sideOffset={sideOffset}
      className={cn(
        '.fmtm-z-50 fmtm-min-w-[8rem] fmtm-overflow-hidden fmtm-rounded-md fmtm-border fmtm-bg-popover fmtm-p-1 fmtm-text-popover-foreground fmtm-shadow-md data-[state=open]:fmtm-animate-in data-[state=closed]:fmtm-animate-out data-[state=closed]:fmtm-fade-out-0 data-[state=open]:fmtm-fade-in-0 data-[state=closed]:fmtm-zoom-out-95 data-[state=open]:fmtm-zoom-in-95 data-[side=bottom]:fmtm-slide-in-from-top-2 data-[side=left]:fmtm-slide-in-from-right-2 data-[side=right]:fmtm-slide-in-from-left-2 data-[side=top]:fmtm-slide-in-from-bottom-2',
        className,
      )}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
);
DropdownMenuContent.displayName = DropdownMenuPrimitive.Content.displayName;

const DropdownMenuItem = ({ ...props }) => (
  <DropdownMenuPrimitive.Item
    className={cn(
      'fmtm-relative fmtm-flex fmtm-cursor-pointer fmtm-select-none fmtm-items-center fmtm-rounded-sm fmtm-px-2 fmtm-py-1.5 fmtm-text-sm fmtm-outline-none fmtm-transition-colors focus:fmtm-bg-red-light focus:fmtm-text-black data-[disabled]:fmtm-pointer-events-none data-[disabled]:fmtm-opacity-50',
    )}
    {...props}
  />
);
DropdownMenuItem.displayName = DropdownMenuPrimitive.Item.displayName;

const DropdownMenuCheckboxItem = ({ className, children, checked, ref, ...props }) => (
  <DropdownMenuPrimitive.CheckboxItem
    ref={ref}
    className={cn(
      'fmtm-relative fmtm-flex fmtm-cursor-default fmtm-select-none fmtm-items-center fmtm-rounded-sm fmtm-py-1.5 fmtm-pl-8 fmtm-pr-2 fmtm-text-sm fmtm-outline-none fmtm-transition-colors fmtm-focus:bg-accent fmtm-focus:text-accent-foreground data-[disabled]:fmtm-pointer-events-none data-[disabled]:fmtm-opacity-50',
      className,
    )}
    checked={checked}
    {...props}
  >
    <span className="fmtm-absolute left-2 fmtm-flex fmtm-h-3.5 fmtm-w-3.5 fmtm-items-center fmtm-justify-center">
      <DropdownMenuPrimitive.ItemIndicator>
        <CheckIcon className="fmtm-h-4 fmtm-w-4" />
      </DropdownMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </DropdownMenuPrimitive.CheckboxItem>
);
DropdownMenuCheckboxItem.displayName = DropdownMenuPrimitive.CheckboxItem.displayName;

const DropdownMenuRadioItem = ({ className, children, ref, ...props }) => (
  <DropdownMenuPrimitive.RadioItem
    ref={ref}
    className={cn(
      'relative fmtm-flex fmtm-cursor-default fmtm-select-none fmtm-items-center fmtm-rounded-sm fmtm-py-1.5 fmtm-pl-8 fmtm-pr-2 fmtm-text-sm fmtm-outline-none fmtm-transition-colors fmtm-focus:bg-accent fmtm-focus:text-accent-foreground data-[disabled]:fmtm-pointer-events-none data-[disabled]:fmtm-opacity-50',
      className,
    )}
    {...props}
  >
    <span className="absolute left-2 fmtm-flex fmtm-h-3.5 fmtm-w-3.5 fmtm-items-center fmtm-justify-center">
      <DropdownMenuPrimitive.ItemIndicator>
        <DotFilledIcon className="h-4 w-4 fill-current" />
      </DropdownMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </DropdownMenuPrimitive.RadioItem>
);
DropdownMenuRadioItem.displayName = DropdownMenuPrimitive.RadioItem.displayName;

const DropdownMenuLabel = ({ className, inset, ref, ...props }) => (
  <DropdownMenuPrimitive.Label
    ref={ref}
    className={cn('fmtm-px-2 fmtm-py-1.5 fmtm-text-sm fmtm-font-semibold', inset && 'fmtm-pl-8', className)}
    {...props}
  />
);
DropdownMenuLabel.displayName = DropdownMenuPrimitive.Label.displayName;

const DropdownMenuSeparator = ({ className, ref, ...props }) => (
  <DropdownMenuPrimitive.Separator
    ref={ref}
    className={cn('fmtm--mx-1 fmtm-my-1 fmtm-h-px fmtm-bg-muted', className)}
    {...props}
  />
);
DropdownMenuSeparator.displayName = DropdownMenuPrimitive.Separator.displayName;

const DropdownMenuShortcut = ({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) => {
  return (
    <span className={cn('fmtm-ml-auto fmtm-text-xs fmtm-tracking-widest fmtm-opacity-60', className)} {...props} />
  );
};
DropdownMenuShortcut.displayName = 'DropdownMenuShortcut';

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuGroup,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
};
