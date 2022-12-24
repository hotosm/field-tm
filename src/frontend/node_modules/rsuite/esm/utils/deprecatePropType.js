// Ref: https://github.com/thefrontside/deprecated-prop-type/blob/master/deprecated.js
import warnOnce from './warnOnce';
export default function deprecatePropType(propType, explanation) {
  return function validate(props, propName, componentName) {
    // Note ...rest here
    if (props[propName] != null) {
      var message = "\"" + propName + "\" property of \"" + componentName + "\" has been deprecated.\n" + explanation;
      warnOnce(message);
    }

    for (var _len = arguments.length, rest = new Array(_len > 3 ? _len - 3 : 0), _key = 3; _key < _len; _key++) {
      rest[_key - 3] = arguments[_key];
    }

    return propType.apply(void 0, [props, propName, componentName].concat(rest)); // and here
  };
}