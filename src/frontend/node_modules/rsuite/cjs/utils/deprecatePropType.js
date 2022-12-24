"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");

exports.__esModule = true;
exports.default = deprecatePropType;

var _warnOnce = _interopRequireDefault(require("./warnOnce"));

// Ref: https://github.com/thefrontside/deprecated-prop-type/blob/master/deprecated.js
function deprecatePropType(propType, explanation) {
  return function validate(props, propName, componentName) {
    // Note ...rest here
    if (props[propName] != null) {
      var message = "\"" + propName + "\" property of \"" + componentName + "\" has been deprecated.\n" + explanation;
      (0, _warnOnce.default)(message);
    }

    for (var _len = arguments.length, rest = new Array(_len > 3 ? _len - 3 : 0), _key = 3; _key < _len; _key++) {
      rest[_key - 3] = arguments[_key];
    }

    return propType.apply(void 0, [props, propName, componentName].concat(rest)); // and here
  };
}