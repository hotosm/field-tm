
interface ProjectValues {
  xform_title: string;
  form_ways: string;
  data_extractWays: string;
  data_extractFile: object;
}
interface ValidationErrors {
  xform_title?: string;
  form_ways?: string;
  data_extractWays?: string;
  data_extractFile?: string;
}

function DataExtractValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.xform_title) {
    errors.xform_title = 'Form Category is Required.';
  }
  if(values.data_extractWays || values.data_extractFile){
  }else{
    errors.data_extractWays = 'Data Extract Ways is Required.';
    
  }


  console.log(errors);
  return errors;
}

export default DataExtractValidation;
