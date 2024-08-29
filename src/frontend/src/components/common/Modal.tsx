import * as React from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { X } from 'lucide-react';

import { cn } from '@/utilfunctions/shadcn';

const Dialog = DialogPrimitive.Root;

const DialogTrigger = DialogPrimitive.Trigger;

const DialogPortal = ({ ...props }: DialogPrimitive.DialogPortalProps) => <DialogPrimitive.Portal {...props} />;
DialogPortal.displayName = DialogPrimitive.Portal.displayName;

const DialogOverlay = ({
  className,
  ref,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      'fmtm-fixed fmtm-inset-0 fmtm-bg-black fmtm-opacity-80 fmtm-backdrop-blur-sm data-[state=open]:fmtm-animate-in data-[state=closed]:fmtm-animate-out data-[state=closed]:fmtm-fade-out-0 data-[state=open]:fmtm-fade-in-0 fmtm-z-[99998]',
      className,
    )}
    {...props}
  />
);
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

interface IModalProps {
  dialogOpen?: React.FC<any>;
  title?: React.ReactNode;
  description: React.ReactNode;
  open: boolean;
  className: string;
  onOpenChange: (open: boolean) => void;
}

const DialogContent = ({
  className,
  children,
  ref,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        'fmtm-fixed fmtm-left-[50%] fmtm-top-[50%]  fmtm-grid fmtm-w-full fmtm-max-w-lg fmtm-translate-x-[-50%] fmtm-translate-y-[-50%] fmtm-gap-4 fmtm-border fmtm-bg-white fmtm-p-6 fmtm-shadow-lg fmtm-duration-200 data-[state=open]:fmtm-animate-in data-[state=closed]:fmtm-animate-out data-[state=closed]:fmtm-fade-out-0 data-[state=open]:fmtm-fade-in-0 data-[state=closed]:fmtm-zoom-out-95 data-[state=open]:fmtm-zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:fmtm-slide-in-from-left-1/2 data-[state=open]:fmtm-slide-in-from-top-[48%] fmtm-sm:rounded-lg fmtm-md:w-full fmtm-z-[99999]',
        className,
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="fmtm-absolute fmtm-right-4 fmtm-top-4 fmtm-rounded-sm fmtm-opacity-70 fmtm-ring-offset-black fmtm-transition-opacity hover:fmtm-opacity-100 focus:fmtm-outline-none disabled:fmtm-pointer-events-none data-[state=open]:fmtm-bg-white data-[state=open]:fmtm-text-black  fmtm-w-fit">
        <X className="fmtm-h-4 fmtm-w-4" />
        <span className="fmtm-sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
);
DialogContent.displayName = DialogPrimitive.Content.displayName;

const DialogHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn('fmtm-flex fmtm-flex-col fmtm-space-y-1.5 fmtm-text-center fmtm-sm:text-left', className)}
    {...props}
  />
);
DialogHeader.displayName = 'DialogHeader';

const DialogFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn('fmtm-flex fmtm-flex-col-reverse fmtm-sm:flex-row fmtm-sm:justify-end fmtm-sm:space-x-2', className)}
    {...props}
  />
);
DialogFooter.displayName = 'DialogFooter';

const DialogTitle = ({ className, ref, ...props }: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn('fmtm-text-lg fmtm-font-semibold fmtm-leading-none fmtm-tracking-tight', className)}
    {...props}
  />
);
DialogTitle.displayName = DialogPrimitive.Title.displayName;

const DialogDescription = ({
  className,
  ref,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>) => (
  <DialogPrimitive.Description ref={ref} className={cn('fmtm-text-sm fmtm-text-black', className)} {...props} />
);
DialogDescription.displayName = DialogPrimitive.Description.displayName;

const Modal = ({ dialogOpen, title, description, open, onOpenChange, className }: IModalProps) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {dialogOpen && <DialogTrigger>{dialogOpen}</DialogTrigger>}
      <DialogContent className={`${className}`}>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription className="!fmtm-text-left">{description}</DialogDescription>
        </DialogHeader>
      </DialogContent>
    </Dialog>
  );
};

export { Modal, Dialog, DialogTrigger, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription };
