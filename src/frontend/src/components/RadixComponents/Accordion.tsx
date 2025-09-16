import * as React from 'react';
import * as AccordionPrimitive from '@radix-ui/react-accordion';
import { ChevronDownIcon } from 'lucide-react';
import '../../index.css';

import { cn } from '@/utilfunctions/shadcn';

function Accordion({ ...props }: React.ComponentProps<typeof AccordionPrimitive.Root>) {
  return <AccordionPrimitive.Root data-slot="accordion" {...props} />;
}

function AccordionItem({ className, ...props }: React.ComponentProps<typeof AccordionPrimitive.Item>) {
  return (
    <AccordionPrimitive.Item
      data-slot="accordion-item"
      className={cn('fmtm-border-b last:fmtm-border-b-0', className)}
      {...props}
    />
  );
}

function AccordionTrigger({ className, children, ...props }: React.ComponentProps<typeof AccordionPrimitive.Trigger>) {
  return (
    <AccordionPrimitive.Header className="fmtm-flex">
      <AccordionPrimitive.Trigger
        data-slot="accordion-trigger"
        className={cn(
          'focus-visible:fmtm-border-ring focus-visible:fmtm-ring-ring/50 fmtm-flex fmtm-flex-1 fmtm-items-start fmtm-justify-between fmtm-gap-4 fmtm-rounded-md fmtm-py-4 fmtm-text-left fmtm-text-sm fmtm-font-medium fmtm-transition-all fmtm-outline-none hover:fmtm-underline focus-visible:fmtm-ring-[3px] disabled:fmtm-pointer-events-none disabled:fmtm-opacity-50 [&[data-state=open]>svg]:fmtm-rotate-180',
          className,
        )}
        {...props}
      >
        {children}
        <ChevronDownIcon className="fmtm-text-grey-700 fmtm-pointer-events-none fmtm-size-4 fmtm-shrink-0 fmtm-translate-y-0.5 fmtm-transition-transform fmtm-duration-200" />
      </AccordionPrimitive.Trigger>
    </AccordionPrimitive.Header>
  );
}

function AccordionContent({ className, children, ...props }: React.ComponentProps<typeof AccordionPrimitive.Content>) {
  return (
    <AccordionPrimitive.Content
      data-slot="accordion-content"
      className="data-[state=closed]:fmtm-animate-accordion-up data-[state=open]:fmtm-animate-accordion-down fmtm-overflow-hidden fmtm-text-sm"
      {...props}
    >
      <div className={cn('fmtm-pt-0 fmtm-pb-4', className)}>{children}</div>
    </AccordionPrimitive.Content>
  );
}

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent };
