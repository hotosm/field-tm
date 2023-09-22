interface ProjectValues {
  splitting_algorithm: string;
  dimension: number;
}
interface ValidationErrors {
  splitting_algorithm?: string;
  dimension?: string;
}

function DefineTaskValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.splitting_algorithm) {
    errors.splitting_algorithm = 'Splitting Algorithm is Required.';
  }
  if (values?.splitting_algorithm === 'Divide on Square' && !values?.dimension) {
    errors.dimension = 'Dimension is Required.';
  }
  if (values?.splitting_algorithm === 'Divide on Square' && values?.dimension && values.dimension < 9) {
    errors.dimension = 'Dimension should be greater than 10 or equal to 10.';
  }

  console.log(errors);
  return errors;
}

export default DefineTaskValidation;
