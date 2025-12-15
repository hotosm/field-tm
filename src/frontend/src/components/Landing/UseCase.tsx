import React from 'react';
import MappingImg from '@/assets/images/landing-pic-2.jpg';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/RadixComponents/Accordion';
import { motion } from 'motion/react';

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
      'Field Tasking Manager can support in building smarter cities by streamlining data collection on houses, roads, and utilities. By coordinating through small manageable tasks, Field TM ensures accurate, scalable, and collaborative mapping for better decision-making in urban development.',
  },
  {
    title: '3. Disaster Response & Recovery',
    description:
      'Field Tasking Manager enables rapid mapping of damaged buildings, roads, and critical infrastructure after disasters. It helps coordinate volunteers, streamline field surveys, and provide accurate data to guide relief and recovery efforts.',
  },
];

const UseCase = () => {
  return (
    <div className="fmtm-flex fmtm-px-[2rem] sm:fmtm-px-[3rem] md:fmtm-px-[4.5rem] fmtm-gap-10 md:fmtm-flex-row fmtm-flex-col-reverse">
      <motion.img
        src={MappingImg}
        className="fmtm-w-[14rem] md:fmtm-w-[18.75rem] lg:fmtm-w-[22rem] fmtm-h-fit fmtm-rounded-2xl fmtm-mx-auto"
        alt="Field mapping in tokha"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
      />
      <div className="fmtm-flex-1">
        <motion.h4
          className="fmtm-mb-3"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          Field-TM Use Cases
        </motion.h4>
        <div>
          <Accordion type="multiple" defaultValue={['item-0', 'item-1', 'item-2']}>
            {useCaseList.map((useCase, index) => (
              <motion.div
                key={index}
                initial={{ x: 10, y: 20, opacity: 0 }}
                whileInView={{ x: 0, y: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.2 }}
              >
                <AccordionItem key={index} value={`item-${index}`}>
                  <AccordionTrigger className="hover:fmtm-no-underline">
                    <h5 className="fmtm-font-medium">{useCase.title}</h5>
                  </AccordionTrigger>
                  <AccordionContent>
                    <p className="fmtm-text-base">{useCase.description}</p>
                  </AccordionContent>
                </AccordionItem>
              </motion.div>
            ))}
          </Accordion>
        </div>
      </div>
    </div>
  );
};

export default UseCase;
