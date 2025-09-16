import React from 'react';
import MappingImg from '@/assets/images/landing-pic-2.jpg';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/RadixComponents/Accordion';

type useCaseType = {
  title: string;
  description: string;
};

const useCaseList: useCaseType[] = [
  {
    title: '1. Community Mapping',
    description:
      'Field Tasking Manager empowers communities to map informal settlements, public facilities, and local services. It supports participatory data collection, ensuring that community needs and resources are accurately represented for inclusive planning.',
  },
  {
    title: '2. Urban Planning and Management',
    description:
      'Field Tasking Manager can support in building smarter cities by streamlining data collection on houses, roads, and utilities. By coordinating through small managable tasks, Field TM ensures accurate, scalable, and collaborative mapping for better decision-making in urban development.',
  },
  {
    title: '3. Disaster Response & Recovery',
    description:
      'Field Tasking Manager enables rapid mapping of damaged buildings, roads, and critical infrastructure after disasters. It helps coordinate volunteers, streamline field surveys, and provide accurate data to guide relief and recovery efforts.',
  },
];

const UseCase = () => {
  return (
    <div className="fmtm-flex fmtm-px-[3rem] md:fmtm-px-[4.5rem] fmtm-gap-10 md:fmtm-flex-row fmtm-flex-col-reverse">
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
