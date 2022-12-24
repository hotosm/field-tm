import _extends from "@babel/runtime/helpers/esm/extends";
import _taggedTemplateLiteralLoose from "@babel/runtime/helpers/esm/taggedTemplateLiteralLoose";
import _objectWithoutPropertiesLoose from "@babel/runtime/helpers/esm/objectWithoutPropertiesLoose";

var _templateObject;

import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ButtonGroupContext } from '../ButtonGroup';
import SafeAnchor from '../SafeAnchor';
import Ripple from '../Ripple';
import { isOneOf, useClassNames } from '../utils';
var Button = /*#__PURE__*/React.forwardRef(function (props, ref) {
  var as = props.as,
      active = props.active,
      _props$appearance = props.appearance,
      appearance = _props$appearance === void 0 ? 'default' : _props$appearance,
      block = props.block,
      className = props.className,
      children = props.children,
      _props$classPrefix = props.classPrefix,
      classPrefix = _props$classPrefix === void 0 ? 'btn' : _props$classPrefix,
      color = props.color,
      disabled = props.disabled,
      loading = props.loading,
      _props$ripple = props.ripple,
      ripple = _props$ripple === void 0 ? true : _props$ripple,
      sizeProp = props.size,
      typeProp = props.type,
      rest = _objectWithoutPropertiesLoose(props, ["as", "active", "appearance", "block", "className", "children", "classPrefix", "color", "disabled", "loading", "ripple", "size", "type"]);

  var buttonGroup = useContext(ButtonGroupContext);
  var size = sizeProp !== null && sizeProp !== void 0 ? sizeProp : buttonGroup === null || buttonGroup === void 0 ? void 0 : buttonGroup.size;

  var _useClassNames = useClassNames(classPrefix),
      withClassPrefix = _useClassNames.withClassPrefix,
      prefix = _useClassNames.prefix,
      merge = _useClassNames.merge;

  var classes = merge(className, withClassPrefix(appearance, color, size, {
    active: active,
    disabled: disabled,
    loading: loading,
    block: block
  }));
  var rippleElement = ripple && !isOneOf(appearance, ['link', 'ghost']) ? /*#__PURE__*/React.createElement(Ripple, null) : null;
  var spin = /*#__PURE__*/React.createElement("span", {
    className: prefix(_templateObject || (_templateObject = _taggedTemplateLiteralLoose(["spin"])))
  });

  if (rest.href) {
    return /*#__PURE__*/React.createElement(SafeAnchor, _extends({}, rest, {
      as: as,
      ref: ref,
      "aria-disabled": disabled,
      disabled: disabled,
      className: classes
    }), loading && spin, children, rippleElement);
  }

  var Component = as || 'button';
  var type = typeProp || (Component === 'button' ? 'button' : undefined);
  var role = rest.role || (Component !== 'button' ? 'button' : undefined);
  return /*#__PURE__*/React.createElement(Component, _extends({}, rest, {
    role: role,
    type: type,
    ref: ref,
    disabled: disabled,
    "aria-disabled": disabled,
    className: classes
  }), loading && spin, children, rippleElement);
});
Button.displayName = 'Button';
Button.propTypes = {
  as: PropTypes.elementType,
  active: PropTypes.bool,
  appearance: PropTypes.oneOf(['default', 'primary', 'link', 'subtle', 'ghost']),
  block: PropTypes.bool,
  children: PropTypes.node,
  color: PropTypes.oneOf(['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'violet']),
  disabled: PropTypes.bool,
  href: PropTypes.string,
  loading: PropTypes.bool,
  ripple: PropTypes.bool,
  size: PropTypes.oneOf(['lg', 'md', 'sm', 'xs']),
  type: PropTypes.oneOf(['button', 'reset', 'submit'])
};
export default Button;