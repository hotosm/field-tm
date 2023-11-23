import { task_split_type } from '../../../types/enums';

interface ProjectValues {
  task_split_type: number;
  dimension: number;
  average_buildings_per_task: number;
}
interface ValidationErrors {
  task_split_type?: string;
  dimension?: string;
  average_buildings_per_task?: string;
}

function DefineTaskValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};
  if (
    values?.task_split_type !== task_split_type['choose_area_as_task'] &&
    values?.task_split_type !== task_split_type['divide_on_square'] &&
    values?.task_split_type !== task_split_type['task_splitting_algorithm']
  ) {
    errors.task_split_type = 'Splitting Algorithm is required.';
  }
  if (values?.task_split_type === task_split_type['divide_on_square'] && !values?.dimension) {
    errors.dimension = 'Dimension is Required.';
  }
  if (values?.task_split_type === task_split_type['divide_on_square'] && values?.dimension && values.dimension < 9) {
    errors.dimension = 'Dimension should be greater than 10 or equal to 10.';
  }
  if (values?.task_split_type === task_split_type['task_splitting_algorithm'] && !values?.average_buildings_per_task) {
    errors.average_buildings_per_task = 'Average number of buildings per task is required.';
  }

  return errors;
}

export default DefineTaskValidation;
