interface ProjectValues {
  splitTaskOption: string;
  dimension: number;
  average_buildings_per_task: number;
}
interface ValidationErrors {
  splitTaskOption?: string;
  dimension?: string;
  average_buildings_per_task?: string;
}

function DefineTaskValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.splitTaskOption) {
    errors.splitTaskOption = 'Splitting Task Option is required.';
  }
  if (values?.splitTaskOption === 'divide_on_square' && !values?.dimension) {
    errors.dimension = 'Dimension is Required.';
  }
  if (values?.splitTaskOption === 'divide_on_square' && values?.dimension && values.dimension < 9) {
    errors.dimension = 'Dimension should be greater than 10 or equal to 10.';
  }
  if (values?.splitTaskOption === 'task_splitting_algorithm' && !values?.average_buildings_per_task) {
    errors.average_buildings_per_task = 'Average number of buildings per task is required.';
  }
  if (values?.splitTaskOption === 'task_splitting_algorithm' && !values?.average_buildings_per_task) {
    errors.average_buildings_per_task = 'Average number of buildings per task is required.';
  }

  console.log(errors);
  return errors;
}

export default DefineTaskValidation;
