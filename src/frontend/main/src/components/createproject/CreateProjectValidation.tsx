/* eslint-disable camelcase */
function CreateProjectValidation(values) {
    // eslint-disable-next-line no-console
    console.log('values: ', values);
    const emailCondition = /\S+@\S+\.\S+/;
    const errors = {};
  
    if (!values?.name) {
      errors.name = 'Project Name is Required.';
    }
  
    if (!values?.username) {
      errors.username = 'Username is Required.';
    }
    if (!values?.id) {
      errors.id = 'User Id is Required.';
    }
    if (!values?.short_description) {
      errors.short_description = 'Short Description is Required.';
    }
    if (!values?.description) {
      errors.description = 'Description is Required.';
    }
  
    // if (!values?.code) {
    //   errors.code = 'Code is Required.';
    // }category
  
    
    console.log('errors: ', errors);
    return errors;
  }
  
  export default CreateProjectValidation;
  