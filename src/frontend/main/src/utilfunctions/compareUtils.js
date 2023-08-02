function diffObject(firstObject, secondObject) {
  const diffObj = Object.keys(secondObject).reduce((diff, key) => {
    if (firstObject[key] === secondObject[key]) return diff;
    return {
      ...diff,
      [key]: secondObject[key],
    };
  }, {});
  return diffObj;
}
function diffArray(array1, array2) {
  return array1.filter((object1) => !array2.some((object2) => object1.id === object2.id));
}

export { diffArray, diffObject };
