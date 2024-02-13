import React from 'react';

type consentQuestionsType = {
  id: string;
  type: 'radio' | 'checkbox';
  required: boolean;
  question: string;
  description: string | null;
  options: any[];
};

export const consentQuestions: consentQuestionsType[] = [
  {
    id: 'give_consent',
    type: 'radio',
    required: true,
    question: 'Do you give consent?',
    description: null,
    options: [
      {
        name: 'give_consent',
        value: 'yes',
        label: 'Yes, I agree to provide consent to collect, store and process information I provide',
      },
      {
        name: 'give_consent',
        value: 'no',
        label: 'No, I do not agree to provide consent to collect, store and process information I provide',
      },
    ],
  },
  {
    id: 'review_documentation',
    type: 'checkbox',
    required: true,
    question: 'Please review the following documentation...?',
    description: 'Check each box after you have reviewed the material',
    options: [
      {
        id: 'code_of_conduct',
        label: (
          <span>
            Code of Conduct
            <a
              href="https://www.hotosm.org/code-of-conduct"
              className="fmtm-text-primaryRed hover:fmtm-text-red-700 fmtm-cursor-pointer fmtm-w-fit"
              target="_"
            >
              {' '}
              https://www.hotosm.org/code-of-conduct
            </a>
          </span>
        ),
      },
      {
        id: 'learn_osm',
        label: (
          <span>
            LearnOSM
            <a
              href="https://learnosm.org/en/coordination/humanitarian/"
              className="fmtm-text-primaryRed hover:fmtm-text-red-700 fmtm-cursor-pointer fmtm-w-fit"
              target="_"
            >
              {' '}
              https://learnosm.org/en/coordination/humanitarian/{' '}
            </a>
            and associated modules
          </span>
        ),
      },
      {
        id: 'compliance_guide',
        label: (
          <span>
            HOT Suggested OEG Compliance Guide{' '}
            <a
              href="https://docs.google.com/document/d/1IIrR75Cmy92giXLa9hCVIur0wJ3HU4nTZoq6zQWyrEU/edit?usp=sharing"
              className="fmtm-text-primaryRed hover:fmtm-text-red-700 fmtm-cursor-pointer fmtm-w-fit"
              target="_"
            >
              {' '}
              https://docs.google.com/document/d/1IIrR75Cmy92giXLa9hCVIur0wJ3HU4nTZoq6zQWyrEU/edit?usp=sharing
            </a>
          </span>
        ),
      },
    ],
  },
  {
    id: 'log_into',
    type: 'checkbox',
    required: true,
    question: 'Also, please log-into...?',
    description:
      'You do not have to map/take any action - logging in adds your username to the TM database for permissions, etc.',
    options: [
      {
        id: 'staging_site',
        label: (
          <span>
            The staging site{' '}
            <a
              href="https://stage.fmtm.hotosm.org/"
              className="fmtm-text-primaryRed hover:fmtm-text-red-700 fmtm-cursor-pointer fmtm-w-fit"
              target="_"
            >
              {' '}
              https://stage.fmtm.hotosm.org/
            </a>
          </span>
        ),
      },
      {
        id: 'main_site',
        label: (
          <span>
            The main Field Mapping Tasking Manager{' '}
            <a
              href="https://fmtm.hotosm.org/"
              className="fmtm-text-primaryRed hover:fmtm-text-red-700 fmtm-cursor-pointer fmtm-w-fit"
              target="_"
            >
              https://fmtm.hotosm.org/
            </a>
          </span>
        ),
      },
    ],
  },
  {
    id: 'participated_in',
    type: 'checkbox',
    required: false,
    question: 'Have you participated in...?',
    description: 'These are not required but helpful in assessing on-boarding pathways.',
    options: [
      { id: 'mapathon', label: 'Participated in a Mapathon (in person or remote)' },
      { id: 'field_survey', label: 'Organized or helped facilitate a Field Survey (in person or remote)' },
      { id: 'validation_qa', label: 'Organized or helped coordinate a validation / quality assurance effort' },
      { id: 'tm_josm', label: 'Contributed to OpenStreetMap via different mapping tools such as TM, JOSM' },
    ],
  },
];
