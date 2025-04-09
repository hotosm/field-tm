import * as React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/RadixComponents/Dialog';

interface IModalProps {
  dialogOpen?: React.ReactNode;
  title?: React.ReactNode;
  description: React.ReactNode;
  open: boolean;
  className: string;
  onOpenChange: (open: boolean) => void;
}

export const Modal = ({ dialogOpen, title, description, open, onOpenChange, className }: IModalProps) => {
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
