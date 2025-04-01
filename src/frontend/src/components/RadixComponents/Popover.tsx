import React from 'react';
import * as PopoverPrimitive from '@radix-ui/react-popover';

import { cn } from '@/utilfunctions/shadcn';

const Popover = PopoverPrimitive.Root;

const PopoverTrigger = PopoverPrimitive.Trigger;

const PopoverArrow = PopoverPrimitive.Arrow;

const PopoverContent = React.forwardRef<
  React.ElementRef<typeof PopoverPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Content>
>(({ className, align = 'center', sideOffset = 4, ...props }, ref) => (
  <PopoverPrimitive.Portal>
    <PopoverPrimitive.Content
      ref={ref}
      align={align}
      sideOffset={sideOffset}
      className={cn(
        'bg-popover text-popover-foreground data-[side=left]:fmtm-slide-in-from-right-2 data-[side=right]:fmtm-slide-in-from-left-2 data-[side=top]:fmtm-slide-in-from-bottom-2 fmtm-z-50 fmtm-w-72 fmtm-rounded-md fmtm-border fmtm-p-4 fmtm-shadow-md fmtm-outline-none data-[state=closed]:fmtm-animate-fade-up-hide data-[state=open]:fmtm-animate-fade-down',
        className,
      )}
      {...props}
    />
  </PopoverPrimitive.Portal>
));
PopoverContent.displayName = PopoverPrimitive.Content.displayName;

export { Popover, PopoverTrigger, PopoverContent, PopoverArrow };
