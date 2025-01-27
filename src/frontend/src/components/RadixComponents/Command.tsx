/* eslint-disable react/jsx-props-no-spreading */
import React from 'react';
import { DialogProps } from '@radix-ui/react-dialog';
import { Command as CommandPrimitive } from 'cmdk';
import { Search } from 'lucide-react';

import { cn } from '@/utilfunctions/shadcn';
import { Dialog, DialogContent } from './Dialog';

const Command = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive>
>(({ className, ...props }, ref) => (
  <CommandPrimitive
    ref={ref}
    className={cn(
      'bg-popover fmtm-flex fmtm-h-full fmtm-w-full fmtm-flex-col fmtm-overflow-hidden fmtm-rounded-md',
      className,
    )}
    {...props}
  />
));
Command.displayName = CommandPrimitive.displayName;

interface CommandDialogProps extends DialogProps {}

const CommandDialog = ({ children, ...props }: CommandDialogProps) => {
  return (
    <Dialog {...props}>
      <DialogContent className="fmtm-overflow-hidden fmtm-p-0 fmtm-shadow-2xl">
        <Command className="[&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:fmtm-px-2 [&_[cmdk-group-heading]]:fmtm-font-medium [&_[cmdk-group]:not([hidden])_~[cmdk-group]]:fmtm-pt-0 [&_[cmdk-group]]:fmtm-px-2 [&_[cmdk-input-wrapper]_svg]:fmtm-h-5 [&_[cmdk-input-wrapper]_svg]:fmtm-w-5 [&_[cmdk-input]]:fmtm-h-12 [&_[cmdk-item]]:fmtm-px-2 [&_[cmdk-item]]:fmtm-py-3 [&_[cmdk-item]_svg]:fmtm-h-5 [&_[cmdk-item]_svg]:fmtm-w-5">
          {children}
        </Command>
      </DialogContent>
    </Dialog>
  );
};

const CommandInput = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Input>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Input>
>(({ className, ...props }, ref) => (
  <div className="fmtm-flex fmtm-items-center fmtm-border-b fmtm-px-3">
    <Search className="fmtm-mr-2 fmtm-h-4 fmtm-w-4 fmtm-shrink-0 fmtm-opacity-50" />
    <CommandPrimitive.Input
      ref={ref}
      className={cn(
        'placeholder:text-muted-foreground fmtm-flex fmtm-h-11 fmtm-w-full fmtm-rounded-md fmtm-bg-transparent fmtm-py-3 fmtm-text-sm fmtm-outline-none disabled:fmtm-cursor-not-allowed disabled:fmtm-opacity-50',
        className,
      )}
      {...props}
    />
  </div>
));

CommandInput.displayName = CommandPrimitive.Input.displayName;

const CommandList = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.List>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.List
    ref={ref}
    className={cn('fmtm-max-h-[300px] fmtm-overflow-y-auto fmtm-overflow-x-hidden', className)}
    {...props}
  />
));

CommandList.displayName = CommandPrimitive.List.displayName;

const CommandEmpty = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Empty>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Empty>
>((props, ref) => <CommandPrimitive.Empty ref={ref} className="fmtm-py-6 fmtm-text-center fmtm-text-sm" {...props} />);

CommandEmpty.displayName = CommandPrimitive.Empty.displayName;

const CommandGroup = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Group>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Group>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Group
    ref={ref}
    className={cn(
      'text-foreground [&_[cmdk-group-heading]]:text-muted-foreground fmtm-overflow-hidden fmtm-p-1 [&_[cmdk-group-heading]]:fmtm-px-2 [&_[cmdk-group-heading]]:fmtm-py-1.5 [&_[cmdk-group-heading]]:fmtm-text-xs [&_[cmdk-group-heading]]:fmtm-font-medium',
      className,
    )}
    {...props}
  />
));

CommandGroup.displayName = CommandPrimitive.Group.displayName;

const CommandSeparator = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Separator ref={ref} className={cn('fmtm-bg-border -fmtm-mx-1 fmtm-h-px', className)} {...props} />
));
CommandSeparator.displayName = CommandPrimitive.Separator.displayName;

const CommandItem = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Item>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Item
    ref={ref}
    className={cn(
      'aria-selected:bg-accent aria-selected:text-accent-foreground fmtm-relative fmtm-flex fmtm-cursor-default fmtm-select-none fmtm-items-center fmtm-rounded-sm fmtm-px-2 fmtm-py-1.5 fmtm-text-sm fmtm-outline-none hover:fmtm-bg-blue-50',
      className,
    )}
    {...props}
  />
));

CommandItem.displayName = CommandPrimitive.Item.displayName;

const CommandShortcut = ({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) => {
  return (
    <span
      className={cn('text-muted-foreground fmtm-ml-auto fmtm-text-xs fmtm-tracking-widest', className)}
      {...props}
    />
  );
};
CommandShortcut.displayName = 'CommandShortcut';

export {
  Command,
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandShortcut,
  CommandSeparator,
};
