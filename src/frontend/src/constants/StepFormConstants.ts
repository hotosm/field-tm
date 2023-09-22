interface ICreateProjectSteps {
  url: string;
  step: number;
  label: string;
  name: string;
  children?: number;
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
    children: 1,
  },
  {
    url: '/data-extract',
    step: 3,
    label: '03',
    name: 'Data Extract',
    children: 1,
  },
  {
    url: '/define-tasks',
    step: 4,
    label: '04',
    name: 'Split Tasks',
    children: 1,
  },
  {
    url: '/select-form',
    step: 5,
    label: '05',
    name: 'Select Form',
  },
];
