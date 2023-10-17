interface ICreateProjectSteps {
  url: string;
  step: number;
  label: string;
  name: string;
}

export const createProjectSteps: ICreateProjectSteps[] = [
  {
    url: '/create-project',
    step: 1,
    label: '01',
    name: 'Project Details',
  },
  {
    url: '/upload-area',
    step: 2,
    label: '02',
    name: 'Upload Area',
  },
  {
    url: '/select-form',
    step: 3,
    label: '03',
    name: 'Select Form',
  },
  {
    url: '/data-extract',
    step: 4,
    label: '04',
    name: 'Data Extract',
  },
  {
    url: '/split-tasks',
    step: 5,
    label: '05',
    name: 'Split Tasks',
  },
];
