function diffObject(a, b) {
    const diffObj = Object.keys(b).reduce((diff, key) => {
      if (a[key] === b[key]) return diff;
      return {
        ...diff,
        [key]: b[key],
      };
    }, {});
    return diffObj;
  }
  function diffArray(array1, array2) {
    return array1.filter((object1) => !array2.some((object2) => object1.id === object2.id));
  }


  export { diffArray,diffObject };