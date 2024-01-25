import React, { useEffect, useState } from 'react';

const useForm = (initialState, callback, validate) => {
  const [values, setValues] = useState(initialState);
  const [errors, setErrors] = useState({});
  const handleChange = (event) => {
    const { name, value } = event.target;

    setValues((prev) => ({ ...prev, [name]: value }));
    // setErrors(validate({ ...values, [name]: value }));
  };

  const handleCustomChange = (name, value) => {
    setValues((prev) => ({ ...prev, [name]: value }));
    // setErrors(validate({ ...values, [name]: value }));
  };

  const handleAllValues = (value) => {
    setValues(value);
  };
  const checkValidationOnly = (formValues) => {
    const x = validate(formValues);
    console.log(x, 'x');
    console.log(formValues, 'values');
    if (Object.keys(x)?.length === 0) {
      return false;
    } else {
      return true;
    }
  };
  const handleSubmit = (event) => {
    event.preventDefault();
    // setErrors(validate(values));
    // callback();
    const x = validate(values);
    setErrors(x);
    if (Object.keys(x)?.length === 0) {
      callback();
      setValues(initialState);
    }

    // if (values?.bulk_id) {
    //   setErrors({});
    //   setIsSubmitting(true);
    // } else {
    //   setErrors(validate(values));
    //   setIsSubmitting(true);
    // }
  };

  // useEffect(() => {
  //   if (Object.keys(errors).length === 0 && isSubmitting) {
  //     // setErrors(validate(values));
  //     callback();
  //     setValues(initialState);
  //   }
  //   // eslint-disable-next-line react-hooks/exhaustive-deps
  // }, [errors]);
  useEffect(() => {
    setValues(initialState);
    setErrors({});
  }, [initialState]);

  return {
    handleChange,
    handleSubmit,
    values,
    errors,
    handleCustomChange,
    handleAllValues,
    setValues,
    setErrors,
    checkValidationOnly,
  };
};

export default useForm;
