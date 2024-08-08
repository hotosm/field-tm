const diffObject = (firstObject: Record<string, any>, secondObject: Record<string, any>): Record<string, any> => {
  const diffObj = Object.keys(secondObject).reduce((diff, key) => {
    if (firstObject[key] === secondObject[key]) return diff;
    return {
      ...diff,
      [key]: secondObject[key],
    };
  }, {});
  return diffObj;
};

const diffArray = (array1: Record<string, any>[], array2: Record<string, any>[]): Record<string, any>[] => {
  return array1.filter((object1) => !array2.some((object2) => object1.id === object2.id));
};

export { diffArray, diffObject };
