
interface ProjectValues {
  xform_title: string;
  form_ways: string;
  data_extractWays: string;
  data_extractFile: object;
  data_extract_options:string;
}
interface ValidationErrors {
  xform_title?: string;
  form_ways?: string;
  data_extractWays?: string;
  data_extractFile?: string;
  data_extract_options?:string;
}

function DataExtractValidation(values: ProjectValues) {
  const errors: ValidationErrors = {};

  if (!values?.xform_title) {
    errors.xform_title = 'Form Category is Required.';
  }
  if(!values.data_extract_options){
    errors.data_extract_options= 'Select Data Extract Options.';
  }
  if(values.data_extract_options && values.data_extract_options === 'Upload Custom Data Extract' && !values.data_extractFile){
    errors.data_extractFile = 'Data Extract File is Required.';
  }
  if(values.data_extract_options && values.data_extract_options === 'Data Extract Ways' && !values.data_extractWays){
    errors.data_extractWays = 'Data Extract Ways is Required.';
  }


  console.log(errors);
  return errors;
}

export default DataExtractValidation;
