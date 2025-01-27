/* eslint-disable react/jsx-props-no-spreading */
import React from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { cn } from '@/utilfunctions/shadcn';

const Dialog = DialogPrimitive.Root;

const DialogTrigger = DialogPrimitive.Trigger;

const DialogPortal = ({ children, ...props }: DialogPrimitive.DialogPortalProps) => (
  <DialogPrimitive.Portal {...props}>
    <div className="fmtm-fixed fmtm-inset-0 fmtm-z-50 fmtm-flex fmtm-items-start fmtm-justify-center sm:fmtm-items-center">
      {children}
    </div>
  </DialogPrimitive.Portal>
);
DialogPortal.displayName = DialogPrimitive.Portal.displayName;

const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      'fmtm-bg-background/80 fmtm-fixed fmtm-inset-0 fmtm-z-50 fmtm-backdrop-blur-sm fmtm-transition-all fmtm-duration-100 data-[state=closed]:fmtm-animate-out data-[state=closed]:fmtm-fade-out data-[state=open]:fmtm-fade-in',
      className,
    )}
    {...props}
  />
));
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        'fmtm-bg-background fmtm-fixed fmtm-z-50 fmtm-grid fmtm-w-full fmtm-gap-4 fmtm-rounded-b-lg fmtm-border fmtm-p-6 fmtm-shadow-lg fmtm-animate-in data-[state=open]:fmtm-fade-in-90 data-[state=open]:fmtm-slide-in-from-bottom-10 sm:fmtm-max-w-lg sm:fmtm-rounded-lg sm:fmtm-zoom-in-90 data-[state=open]:sm:fmtm-slide-in-from-bottom-0',
        className,
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="fmtm-ring-offset-background focus:fmtm-ring-ring data-[state=open]:bg-accent data-[state=open]:text-muted-foreground fmtm-absolute fmtm-right-4 fmtm-top-4 fmtm-rounded-sm fmtm-opacity-70 fmtm-transition-opacity hover:fmtm-opacity-100 focus:fmtm-outline-none focus:fmtm-ring-2 focus:fmtm-ring-offset-2 disabled:fmtm-pointer-events-none">
        <X className="fmtm-h-4 fmtm-w-4" />
        <span className="sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
));
DialogContent.displayName = DialogPrimitive.Content.displayName;

const DialogHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn('fmtm-flex fmtm-flex-col fmtm-space-y-1.5 fmtm-text-center sm:fmtm-text-left', className)}
    {...props}
  />
);
DialogHeader.displayName = 'DialogHeader';

const DialogFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn('fmtm-flex fmtm-flex-col-reverse sm:fmtm-flex-row sm:fmtm-justify-end sm:fmtm-space-x-2', className)}
    {...props}
  />
);
DialogFooter.displayName = 'DialogFooter';

const DialogTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn('fmtm-text-lg fmtm-font-semibold fmtm-leading-none fmtm-tracking-tight', className)}
    {...props}
  />
));
DialogTitle.displayName = DialogPrimitive.Title.displayName;

const DialogDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description ref={ref} className={cn('text-muted-foreground fmtm-text-sm', className)} {...props} />
));
DialogDescription.displayName = DialogPrimitive.Description.displayName;

export { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription };
