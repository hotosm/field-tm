import React from 'react';
import MappingImg from '@/assets/images/landing-pic-2.jpg';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/RadixComponents/Accordion';

type useCaseType = {
  title: string;
  description: string;
};

const useCaseList: useCaseType[] = [
  {
    title: 'Slum Mapping',
    description: 'Yes. It adheres to the WAI-ARIA design pattern.Yes. It adheres to the WAI-ARIA design pattern.',
  },
  {
    title: 'Urban Management',
    description: 'Yes. It adheres to the WAI-ARIA design pattern.Yes. It adheres to the WAI-ARIA design pattern.',
  },
  {
    title: 'Road Network Survey',
    description: 'Yes. It adheres to the WAI-ARIA design pattern.Yes. It adheres to the WAI-ARIA design pattern.',
  },
];

const UseCase = () => {
  return (
    <div className="fmtm-flex fmtm-px-[3rem] md:fmtm-px-[4.5rem] fmtm-gap-10 fmtm-flex-col md:fmtm-flex-row">
      <img
        src={MappingImg}
        className="fmtm-w-[14rem] md:fmtm-w-[18.75rem] lg:fmtm-w-[22rem] fmtm-h-fit fmtm-rounded-2xl fmtm-mx-auto"
        alt="Field mapping in tokha"
      />
      <div className="fmtm-flex-1">
        <h4 className="fmtm-mb-3">FIELD-TM USE CASES</h4>
        <div>
          <Accordion type="single" collapsible defaultValue="item-0">
            {useCaseList.map((useCase, index) => (
              <AccordionItem key={index} value={`item-${index}`}>
                <AccordionTrigger className="hover:fmtm-no-underline">
                  <h5 className="fmtm-font-medium">{useCase.title}</h5>
                </AccordionTrigger>
                <AccordionContent>
                  <p className="fmtm-text-base">{useCase.description}</p>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </div>
    </div>
  );
};

export default UseCase;
