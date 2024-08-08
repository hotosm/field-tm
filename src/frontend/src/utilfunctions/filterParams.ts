const filterParams = (params: Record<string, any>): Record<string, any> => {
  const filteredParams = {};
  Object.keys(params).forEach((key: string) => {
    if (params[key] !== null && params[key] !== '') {
      filteredParams[key] = params[key];
    }
  });
  return filteredParams;
};

export default filterParams;
