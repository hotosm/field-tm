import _objectWithoutProperties from "@babel/runtime/helpers/esm/objectWithoutProperties";
import _defineProperty from "@babel/runtime/helpers/esm/defineProperty";
import _extends from "@babel/runtime/helpers/esm/extends";
import * as React from 'react';
import PropTypes from 'prop-types';
import clsx from 'clsx';
import { chainPropTypes, unstable_generateUtilityClasses as generateUtilityClasses } from '@mui/utils';
import SliderUnstyled, { SliderValueLabelUnstyled, sliderUnstyledClasses, getSliderUtilityClass } from '@mui/base/SliderUnstyled';
import { alpha, lighten, darken } from '@mui/system';
import useThemeProps from '../styles/useThemeProps';
import styled, { slotShouldForwardProp } from '../styles/styled';
import useTheme from '../styles/useTheme';
import shouldSpreadAdditionalProps from '../utils/shouldSpreadAdditionalProps';
import capitalize from '../utils/capitalize';
import { jsx as _jsx } from "react/jsx-runtime";
export var sliderClasses = _extends({}, sliderUnstyledClasses, generateUtilityClasses('MuiSlider', ['colorPrimary', 'colorSecondary', 'thumbColorPrimary', 'thumbColorSecondary', 'sizeSmall', 'thumbSizeSmall']));
var SliderRoot = styled('span', {
  name: 'MuiSlider',
  slot: 'Root',
  overridesResolver: function overridesResolver(props, styles) {
    var ownerState = props.ownerState;
    return [styles.root, styles["color".concat(capitalize(ownerState.color))], ownerState.size !== 'medium' && styles["size".concat(capitalize(ownerState.size))], ownerState.marked && styles.marked, ownerState.orientation === 'vertical' && styles.vertical, ownerState.track === 'inverted' && styles.trackInverted, ownerState.track === false && styles.trackFalse];
  }
})(function (_ref) {
  var _extends2;
  var theme = _ref.theme,
    ownerState = _ref.ownerState;
  return _extends({
    borderRadius: 12,
    boxSizing: 'content-box',
    display: 'inline-block',
    position: 'relative',
    cursor: 'pointer',
    touchAction: 'none',
    color: (theme.vars || theme).palette[ownerState.color].main,
    WebkitTapHighlightColor: 'transparent'
  }, ownerState.orientation === 'horizontal' && _extends({
    height: 4,
    width: '100%',
    padding: '13px 0',
    // The primary input mechanism of the device includes a pointing device of limited accuracy.
    '@media (pointer: coarse)': {
      // Reach 42px touch target, about ~8mm on screen.
      padding: '20px 0'
    }
  }, ownerState.size === 'small' && {
    height: 2
  }, ownerState.marked && {
    marginBottom: 20
  }), ownerState.orientation === 'vertical' && _extends({
    height: '100%',
    width: 4,
    padding: '0 13px',
    // The primary input mechanism of the device includes a pointing device of limited accuracy.
    '@media (pointer: coarse)': {
      // Reach 42px touch target, about ~8mm on screen.
      padding: '0 20px'
    }
  }, ownerState.size === 'small' && {
    width: 2
  }, ownerState.marked && {
    marginRight: 44
  }), (_extends2 = {
    '@media print': {
      colorAdjust: 'exact'
    }
  }, _defineProperty(_extends2, "&.".concat(sliderClasses.disabled), {
    pointerEvents: 'none',
    cursor: 'default',
    color: (theme.vars || theme).palette.grey[400]
  }), _defineProperty(_extends2, "&.".concat(sliderClasses.dragging), _defineProperty({}, "& .".concat(sliderClasses.thumb, ", & .").concat(sliderClasses.track), {
    transition: 'none'
  })), _extends2));
});
process.env.NODE_ENV !== "production" ? SliderRoot.propTypes /* remove-proptypes */ = {
  // ----------------------------- Warning --------------------------------
  // | These PropTypes are generated from the TypeScript type definitions |
  // |     To update them edit the d.ts file and run "yarn proptypes"     |
  // ----------------------------------------------------------------------
  /**
   * @ignore
   */
  children: PropTypes.node
} : void 0;
export { SliderRoot };
var SliderRail = styled('span', {
  name: 'MuiSlider',
  slot: 'Rail',
  overridesResolver: function overridesResolver(props, styles) {
    return styles.rail;
  }
})(function (_ref2) {
  var ownerState = _ref2.ownerState;
  return _extends({
    display: 'block',
    position: 'absolute',
    borderRadius: 'inherit',
    backgroundColor: 'currentColor',
    opacity: 0.38
  }, ownerState.orientation === 'horizontal' && {
    width: '100%',
    height: 'inherit',
    top: '50%',
    transform: 'translateY(-50%)'
  }, ownerState.orientation === 'vertical' && {
    height: '100%',
    width: 'inherit',
    left: '50%',
    transform: 'translateX(-50%)'
  }, ownerState.track === 'inverted' && {
    opacity: 1
  });
});
process.env.NODE_ENV !== "production" ? SliderRail.propTypes /* remove-proptypes */ = {
  // ----------------------------- Warning --------------------------------
  // | These PropTypes are generated from the TypeScript type definitions |
  // |     To update them edit the d.ts file and run "yarn proptypes"     |
  // ----------------------------------------------------------------------
  /**
   * @ignore
   */
  children: PropTypes.node
} : void 0;
export { SliderRail };
var SliderTrack = styled('span', {
  name: 'MuiSlider',
  slot: 'Track',
  overridesResolver: function overridesResolver(props, styles) {
    return styles.track;
  }
})(function (_ref3) {
  var theme = _ref3.theme,
    ownerState = _ref3.ownerState;
  var color =
  // Same logic as the LinearProgress track color
  theme.palette.mode === 'light' ? lighten(theme.palette[ownerState.color].main, 0.62) : darken(theme.palette[ownerState.color].main, 0.5);
  return _extends({
    display: 'block',
    position: 'absolute',
    borderRadius: 'inherit',
    border: '1px solid currentColor',
    backgroundColor: 'currentColor',
    transition: theme.transitions.create(['left', 'width', 'bottom', 'height'], {
      duration: theme.transitions.duration.shortest
    })
  }, ownerState.size === 'small' && {
    border: 'none'
  }, ownerState.orientation === 'horizontal' && {
    height: 'inherit',
    top: '50%',
    transform: 'translateY(-50%)'
  }, ownerState.orientation === 'vertical' && {
    width: 'inherit',
    left: '50%',
    transform: 'translateX(-50%)'
  }, ownerState.track === false && {
    display: 'none'
  }, ownerState.track === 'inverted' && {
    backgroundColor: theme.vars ? theme.vars.palette.Slider["".concat(ownerState.color, "Track")] : color,
    borderColor: theme.vars ? theme.vars.palette.Slider["".concat(ownerState.color, "Track")] : color
  });
});
process.env.NODE_ENV !== "production" ? SliderTrack.propTypes /* remove-proptypes */ = {
  // ----------------------------- Warning --------------------------------
  // | These PropTypes are generated from the TypeScript type definitions |
  // |     To update them edit the d.ts file and run "yarn proptypes"     |
  // ----------------------------------------------------------------------
  /**
   * @ignore
   */
  children: PropTypes.node
} : void 0;
export { SliderTrack };
var SliderThumb = styled('span', {
  name: 'MuiSlider',
  slot: 'Thumb',
  overridesResolver: function overridesResolver(props, styles) {
    var ownerState = props.ownerState;
    return [styles.thumb, styles["thumbColor".concat(capitalize(ownerState.color))], ownerState.size !== 'medium' && styles["thumbSize".concat(capitalize(ownerState.size))]];
  }
})(function (_ref4) {
  var _extends3;
  var theme = _ref4.theme,
    ownerState = _ref4.ownerState;
  return _extends({
    position: 'absolute',
    width: 20,
    height: 20,
    boxSizing: 'border-box',
    borderRadius: '50%',
    outline: 0,
    backgroundColor: 'currentColor',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: theme.transitions.create(['box-shadow', 'left', 'bottom'], {
      duration: theme.transitions.duration.shortest
    })
  }, ownerState.size === 'small' && {
    width: 12,
    height: 12
  }, ownerState.orientation === 'horizontal' && {
    top: '50%',
    transform: 'translate(-50%, -50%)'
  }, ownerState.orientation === 'vertical' && {
    left: '50%',
    transform: 'translate(-50%, 50%)'
  }, (_extends3 = {
    '&:before': _extends({
      position: 'absolute',
      content: '""',
      borderRadius: 'inherit',
      width: '100%',
      height: '100%',
      boxShadow: (theme.vars || theme).shadows[2]
    }, ownerState.size === 'small' && {
      boxShadow: 'none'
    }),
    '&::after': {
      position: 'absolute',
      content: '""',
      borderRadius: '50%',
      // 42px is the hit target
      width: 42,
      height: 42,
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)'
    }
  }, _defineProperty(_extends3, "&:hover, &.".concat(sliderClasses.focusVisible), {
    boxShadow: "0px 0px 0px 8px ".concat(theme.vars ? "rgba(".concat(theme.vars.palette[ownerState.color].mainChannel, " / 0.16)") : alpha(theme.palette[ownerState.color].main, 0.16)),
    '@media (hover: none)': {
      boxShadow: 'none'
    }
  }), _defineProperty(_extends3, "&.".concat(sliderClasses.active), {
    boxShadow: "0px 0px 0px 14px ".concat(theme.vars ? "rgba(".concat(theme.vars.palette[ownerState.color].mainChannel, " / 0.16)") : alpha(theme.palette[ownerState.color].main, 0.16))
  }), _defineProperty(_extends3, "&.".concat(sliderClasses.disabled), {
    '&:hover': {
      boxShadow: 'none'
    }
  }), _extends3));
});
process.env.NODE_ENV !== "production" ? SliderThumb.propTypes /* remove-proptypes */ = {
  // ----------------------------- Warning --------------------------------
  // | These PropTypes are generated from the TypeScript type definitions |
  // |     To update them edit the d.ts file and run "yarn proptypes"     |
  // ----------------------------------------------------------------------
  /**
   * @ignore
   */
  children: PropTypes.node
} : void 0;
export { SliderThumb };
var SliderValueLabel = styled(SliderValueLabelUnstyled, {
  name: 'MuiSlider',
  slot: 'ValueLabel',
  overridesResolver: function overridesResolver(props, styles) {
    return styles.valueLabel;
  }
})(function (_ref5) {
  var _extends4;
  var theme = _ref5.theme,
    ownerState = _ref5.ownerState;
  return _extends((_extends4 = {}, _defineProperty(_extends4, "&.".concat(sliderClasses.valueLabelOpen), {
    transform: 'translateY(-100%) scale(1)'
  }), _defineProperty(_extends4, "zIndex", 1), _defineProperty(_extends4, "whiteSpace", 'nowrap'), _extends4), theme.typography.body2, {
    fontWeight: 500,
    transition: theme.transitions.create(['transform'], {
      duration: theme.transitions.duration.shortest
    }),
    transform: 'translateY(-100%) scale(0)',
    position: 'absolute',
    backgroundColor: (theme.vars || theme).palette.grey[600],
    borderRadius: 2,
    color: (theme.vars || theme).palette.common.white,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0.25rem 0.75rem'
  }, ownerState.orientation === 'horizontal' && {
    top: '-10px',
    transformOrigin: 'bottom center',
    '&:before': {
      position: 'absolute',
      content: '""',
      width: 8,
      height: 8,
      transform: 'translate(-50%, 50%) rotate(45deg)',
      backgroundColor: 'inherit',
      bottom: 0,
      left: '50%'
    }
  }, ownerState.orientation === 'vertical' && {
    right: '30px',
    top: '24px',
    transformOrigin: 'right center',
    '&:before': {
      position: 'absolute',
      content: '""',
      width: 8,
      height: 8,
      transform: 'translate(-50%, 50%) rotate(45deg)',
      backgroundColor: 'inherit',
      right: '-20%',
      top: '25%'
    }
  }, ownerState.size === 'small' && {
    fontSize: theme.typography.pxToRem(12),
    padding: '0.25rem 0.5rem'
  });
});
process.env.NODE_ENV !== "production" ? SliderValueLabel.propTypes /* remove-proptypes */ = {
  // ----------------------------- Warning --------------------------------
  // | These PropTypes are generated from the TypeScript type definitions |
  // |     To update them edit the d.ts file and run "yarn proptypes"     |
  // ----------------------------------------------------------------------
  /**
   * @ignore
   */
  children: PropTypes.node
} : void 0;
export { SliderValueLabel };
var SliderMark = styled('span', {
  name: 'MuiSlider',
  slot: 'Mark',
  shouldForwardProp: function shouldForwardProp(prop) {
    return slotShouldForwardProp(prop) && prop !== 'markActive';
  },
  overridesResolver: function overridesResolver(props, styles) {
    var markActive = props.markActive;
    return [styles.mark, markActive && styles.markActive];
  }
})(function (_ref6) {
  var theme = _ref6.theme,
    ownerState = _ref6.ownerState,
    markActive = _ref6.markActive;
  return _extends({
    position: 'absolute',
    width: 2,
    height: 2,
    borderRadius: 1,
    backgroundColor: 'currentColor'
  }, ownerState.orientation === 'horizontal' && {
    top: '50%',
    transform: 'translate(-1px, -50%)'
  }, ownerState.orientation === 'vertical' && {
    left: '50%',
    transform: 'translate(-50%, 1px)'
  }, markActive && {
    backgroundColor: (theme.vars || theme).palette.background.paper,
    opacity: 0.8
  });
});
process.env.NODE_ENV !== "production" ? SliderMark.propTypes /* remove-proptypes */ = {
  // ----------------------------- Warning --------------------------------
  // | These PropTypes are generated from the TypeScript type definitions |
  // |     To update them edit the d.ts file and run "yarn proptypes"     |
  // ----------------------------------------------------------------------
  /**
   * @ignore
   */
  children: PropTypes.node
} : void 0;
export { SliderMark };
var SliderMarkLabel = styled('span', {
  name: 'MuiSlider',
  slot: 'MarkLabel',
  shouldForwardProp: function shouldForwardProp(prop) {
    return slotShouldForwardProp(prop) && prop !== 'markLabelActive';
  },
  overridesResolver: function overridesResolver(props, styles) {
    return styles.markLabel;
  }
})(function (_ref7) {
  var theme = _ref7.theme,
    ownerState = _ref7.ownerState,
    markLabelActive = _ref7.markLabelActive;
  return _extends({}, theme.typography.body2, {
    color: (theme.vars || theme).palette.text.secondary,
    position: 'absolute',
    whiteSpace: 'nowrap'
  }, ownerState.orientation === 'horizontal' && {
    top: 30,
    transform: 'translateX(-50%)',
    '@media (pointer: coarse)': {
      top: 40
    }
  }, ownerState.orientation === 'vertical' && {
    left: 36,
    transform: 'translateY(50%)',
    '@media (pointer: coarse)': {
      left: 44
    }
  }, markLabelActive && {
    color: (theme.vars || theme).palette.text.primary
  });
});
process.env.NODE_ENV !== "production" ? SliderMarkLabel.propTypes /* remove-proptypes */ = {
  // ----------------------------- Warning --------------------------------
  // | These PropTypes are generated from the TypeScript type definitions |
  // |     To update them edit the d.ts file and run "yarn proptypes"     |
  // ----------------------------------------------------------------------
  /**
   * @ignore
   */
  children: PropTypes.node
} : void 0;
export { SliderMarkLabel };
var extendUtilityClasses = function extendUtilityClasses(ownerState) {
  var color = ownerState.color,
    size = ownerState.size,
    _ownerState$classes = ownerState.classes,
    classes = _ownerState$classes === void 0 ? {} : _ownerState$classes;
  return _extends({}, classes, {
    root: clsx(classes.root, getSliderUtilityClass("color".concat(capitalize(color))), classes["color".concat(capitalize(color))], size && [getSliderUtilityClass("size".concat(capitalize(size))), classes["size".concat(capitalize(size))]]),
    thumb: clsx(classes.thumb, getSliderUtilityClass("thumbColor".concat(capitalize(color))), classes["thumbColor".concat(capitalize(color))], size && [getSliderUtilityClass("thumbSize".concat(capitalize(size))), classes["thumbSize".concat(capitalize(size))]])
  });
};
var Slider = /*#__PURE__*/React.forwardRef(function Slider(inputProps, ref) {
  var _ref8, _slots$root, _ref9, _slots$rail, _ref10, _slots$track, _ref11, _slots$thumb, _ref12, _slots$valueLabel, _ref13, _slots$mark, _ref14, _slots$markLabel, _slots$input, _slotProps$root, _slotProps$rail, _slotProps$track, _slotProps$thumb, _slotProps$valueLabel, _slotProps$mark, _slotProps$markLabel, _slotProps$input;
  var props = useThemeProps({
    props: inputProps,
    name: 'MuiSlider'
  });
  var theme = useTheme();
  var isRtl = theme.direction === 'rtl';
  var _props$component = props.component,
    component = _props$component === void 0 ? 'span' : _props$component,
    _props$components = props.components,
    components = _props$components === void 0 ? {} : _props$components,
    _props$componentsProp = props.componentsProps,
    componentsProps = _props$componentsProp === void 0 ? {} : _props$componentsProp,
    _props$color = props.color,
    color = _props$color === void 0 ? 'primary' : _props$color,
    _props$size = props.size,
    size = _props$size === void 0 ? 'medium' : _props$size,
    slotProps = props.slotProps,
    slots = props.slots,
    other = _objectWithoutProperties(props, ["component", "components", "componentsProps", "color", "size", "slotProps", "slots"]);
  var ownerState = _extends({}, props, {
    color: color,
    size: size
  });
  var classes = extendUtilityClasses(ownerState);

  // support both `slots` and `components` for backward compatibility
  var RootSlot = (_ref8 = (_slots$root = slots == null ? void 0 : slots.root) != null ? _slots$root : components.Root) != null ? _ref8 : SliderRoot;
  var RailSlot = (_ref9 = (_slots$rail = slots == null ? void 0 : slots.rail) != null ? _slots$rail : components.Rail) != null ? _ref9 : SliderRail;
  var TrackSlot = (_ref10 = (_slots$track = slots == null ? void 0 : slots.track) != null ? _slots$track : components.Track) != null ? _ref10 : SliderTrack;
  var ThumbSlot = (_ref11 = (_slots$thumb = slots == null ? void 0 : slots.thumb) != null ? _slots$thumb : components.Thumb) != null ? _ref11 : SliderThumb;
  var ValueLabelSlot = (_ref12 = (_slots$valueLabel = slots == null ? void 0 : slots.valueLabel) != null ? _slots$valueLabel : components.ValueLabel) != null ? _ref12 : SliderValueLabel;
  var MarkSlot = (_ref13 = (_slots$mark = slots == null ? void 0 : slots.mark) != null ? _slots$mark : components.Mark) != null ? _ref13 : SliderMark;
  var MarkLabelSlot = (_ref14 = (_slots$markLabel = slots == null ? void 0 : slots.markLabel) != null ? _slots$markLabel : components.MarkLabel) != null ? _ref14 : SliderMarkLabel;
  var InputSlot = (_slots$input = slots == null ? void 0 : slots.input) != null ? _slots$input : components.Input;
  var rootSlotProps = (_slotProps$root = slotProps == null ? void 0 : slotProps.root) != null ? _slotProps$root : componentsProps.root;
  var railSlotProps = (_slotProps$rail = slotProps == null ? void 0 : slotProps.rail) != null ? _slotProps$rail : componentsProps.rail;
  var trackSlotProps = (_slotProps$track = slotProps == null ? void 0 : slotProps.track) != null ? _slotProps$track : componentsProps.track;
  var thumbSlotProps = (_slotProps$thumb = slotProps == null ? void 0 : slotProps.thumb) != null ? _slotProps$thumb : componentsProps.thumb;
  var valueLabelSlotProps = (_slotProps$valueLabel = slotProps == null ? void 0 : slotProps.valueLabel) != null ? _slotProps$valueLabel : componentsProps.valueLabel;
  var markSlotProps = (_slotProps$mark = slotProps == null ? void 0 : slotProps.mark) != null ? _slotProps$mark : componentsProps.mark;
  var markLabelSlotProps = (_slotProps$markLabel = slotProps == null ? void 0 : slotProps.markLabel) != null ? _slotProps$markLabel : componentsProps.markLabel;
  var inputSlotProps = (_slotProps$input = slotProps == null ? void 0 : slotProps.input) != null ? _slotProps$input : componentsProps.input;
  return /*#__PURE__*/_jsx(SliderUnstyled, _extends({}, other, {
    isRtl: isRtl,
    slots: {
      root: RootSlot,
      rail: RailSlot,
      track: TrackSlot,
      thumb: ThumbSlot,
      valueLabel: ValueLabelSlot,
      mark: MarkSlot,
      markLabel: MarkLabelSlot,
      input: InputSlot
    },
    slotProps: _extends({}, componentsProps, {
      root: _extends({}, rootSlotProps, shouldSpreadAdditionalProps(RootSlot) && {
        as: component,
        ownerState: _extends({}, rootSlotProps == null ? void 0 : rootSlotProps.ownerState, {
          color: color,
          size: size
        })
      }),
      rail: railSlotProps,
      thumb: _extends({}, thumbSlotProps, shouldSpreadAdditionalProps(ThumbSlot) && {
        ownerState: _extends({}, thumbSlotProps == null ? void 0 : thumbSlotProps.ownerState, {
          color: color,
          size: size
        })
      }),
      track: _extends({}, trackSlotProps, shouldSpreadAdditionalProps(TrackSlot) && {
        ownerState: _extends({}, trackSlotProps == null ? void 0 : trackSlotProps.ownerState, {
          color: color,
          size: size
        })
      }),
      valueLabel: _extends({}, valueLabelSlotProps, shouldSpreadAdditionalProps(ValueLabelSlot) && {
        ownerState: _extends({}, valueLabelSlotProps == null ? void 0 : valueLabelSlotProps.ownerState, {
          color: color,
          size: size
        })
      }),
      mark: markSlotProps,
      markLabel: markLabelSlotProps,
      input: inputSlotProps
    }),
    classes: classes,
    ref: ref
  }));
});
process.env.NODE_ENV !== "production" ? Slider.propTypes /* remove-proptypes */ = {
  // ----------------------------- Warning --------------------------------
  // | These PropTypes are generated from the TypeScript type definitions |
  // |     To update them edit the d.ts file and run "yarn proptypes"     |
  // ----------------------------------------------------------------------
  /**
   * The label of the slider.
   */
  'aria-label': chainPropTypes(PropTypes.string, function (props) {
    var range = Array.isArray(props.value || props.defaultValue);
    if (range && props['aria-label'] != null) {
      return new Error('MUI: You need to use the `getAriaLabel` prop instead of `aria-label` when using a range slider.');
    }
    return null;
  }),
  /**
   * The id of the element containing a label for the slider.
   */
  'aria-labelledby': PropTypes.string,
  /**
   * A string value that provides a user-friendly name for the current value of the slider.
   */
  'aria-valuetext': chainPropTypes(PropTypes.string, function (props) {
    var range = Array.isArray(props.value || props.defaultValue);
    if (range && props['aria-valuetext'] != null) {
      return new Error('MUI: You need to use the `getAriaValueText` prop instead of `aria-valuetext` when using a range slider.');
    }
    return null;
  }),
  /**
   * @ignore
   */
  children: PropTypes.node,
  /**
   * Override or extend the styles applied to the component.
   */
  classes: PropTypes.object,
  /**
   * The color of the component.
   * It supports both default and custom theme colors, which can be added as shown in the
   * [palette customization guide](https://mui.com/material-ui/customization/palette/#adding-new-colors).
   * @default 'primary'
   */
  color: PropTypes /* @typescript-to-proptypes-ignore */.oneOfType([PropTypes.oneOf(['primary', 'secondary']), PropTypes.string]),
  /**
   * The components used for each slot inside.
   *
   * This prop is an alias for the `slots` prop.
   * It's recommended to use the `slots` prop instead.
   *
   * @default {}
   */
  components: PropTypes.shape({
    Input: PropTypes.elementType,
    Mark: PropTypes.elementType,
    MarkLabel: PropTypes.elementType,
    Rail: PropTypes.elementType,
    Root: PropTypes.elementType,
    Thumb: PropTypes.elementType,
    Track: PropTypes.elementType,
    ValueLabel: PropTypes.elementType
  }),
  /**
   * The extra props for the slot components.
   * You can override the existing props or add new ones.
   *
   * This prop is an alias for the `slotProps` prop.
   * It's recommended to use the `slotProps` prop instead, as `componentsProps` will be deprecated in the future.
   *
   * @default {}
   */
  componentsProps: PropTypes.shape({
    input: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    mark: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    markLabel: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    rail: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    root: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    thumb: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    track: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    valueLabel: PropTypes.oneOfType([PropTypes.func, PropTypes.shape({
      children: PropTypes.element,
      className: PropTypes.string,
      open: PropTypes.bool,
      style: PropTypes.object,
      value: PropTypes.number,
      valueLabelDisplay: PropTypes.oneOf(['auto', 'off', 'on'])
    })])
  }),
  /**
   * The default value. Use when the component is not controlled.
   */
  defaultValue: PropTypes.oneOfType([PropTypes.arrayOf(PropTypes.number), PropTypes.number]),
  /**
   * If `true`, the component is disabled.
   * @default false
   */
  disabled: PropTypes.bool,
  /**
   * If `true`, the active thumb doesn't swap when moving pointer over a thumb while dragging another thumb.
   * @default false
   */
  disableSwap: PropTypes.bool,
  /**
   * Accepts a function which returns a string value that provides a user-friendly name for the thumb labels of the slider.
   * This is important for screen reader users.
   * @param {number} index The thumb label's index to format.
   * @returns {string}
   */
  getAriaLabel: PropTypes.func,
  /**
   * Accepts a function which returns a string value that provides a user-friendly name for the current value of the slider.
   * This is important for screen reader users.
   * @param {number} value The thumb label's value to format.
   * @param {number} index The thumb label's index to format.
   * @returns {string}
   */
  getAriaValueText: PropTypes.func,
  /**
   * Indicates whether the theme context has rtl direction. It is set automatically.
   * @default false
   */
  isRtl: PropTypes.bool,
  /**
   * Marks indicate predetermined values to which the user can move the slider.
   * If `true` the marks are spaced according the value of the `step` prop.
   * If an array, it should contain objects with `value` and an optional `label` keys.
   * @default false
   */
  marks: PropTypes.oneOfType([PropTypes.arrayOf(PropTypes.shape({
    label: PropTypes.node,
    value: PropTypes.number.isRequired
  })), PropTypes.bool]),
  /**
   * The maximum allowed value of the slider.
   * Should not be equal to min.
   * @default 100
   */
  max: PropTypes.number,
  /**
   * The minimum allowed value of the slider.
   * Should not be equal to max.
   * @default 0
   */
  min: PropTypes.number,
  /**
   * Name attribute of the hidden `input` element.
   */
  name: PropTypes.string,
  /**
   * Callback function that is fired when the slider's value changed.
   *
   * @param {Event} event The event source of the callback.
   * You can pull out the new value by accessing `event.target.value` (any).
   * **Warning**: This is a generic event not a change event.
   * @param {number | number[]} value The new value.
   * @param {number} activeThumb Index of the currently moved thumb.
   */
  onChange: PropTypes.func,
  /**
   * Callback function that is fired when the `mouseup` is triggered.
   *
   * @param {React.SyntheticEvent | Event} event The event source of the callback. **Warning**: This is a generic event not a change event.
   * @param {number | number[]} value The new value.
   */
  onChangeCommitted: PropTypes.func,
  /**
   * The component orientation.
   * @default 'horizontal'
   */
  orientation: PropTypes.oneOf(['horizontal', 'vertical']),
  /**
   * A transformation function, to change the scale of the slider.
   * @default (x) => x
   */
  scale: PropTypes.func,
  /**
   * The size of the slider.
   * @default 'medium'
   */
  size: PropTypes /* @typescript-to-proptypes-ignore */.oneOfType([PropTypes.oneOf(['small', 'medium']), PropTypes.string]),
  /**
   * The props used for each slot inside the Slider.
   * @default {}
   */
  slotProps: PropTypes.shape({
    input: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    mark: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    markLabel: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    rail: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    root: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    thumb: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    track: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
    valueLabel: PropTypes.oneOfType([PropTypes.func, PropTypes.shape({
      children: PropTypes.element,
      className: PropTypes.string,
      open: PropTypes.bool,
      style: PropTypes.object,
      value: PropTypes.number,
      valueLabelDisplay: PropTypes.oneOf(['auto', 'off', 'on'])
    })])
  }),
  /**
   * The components used for each slot inside the Slider.
   * Either a string to use a HTML element or a component.
   * @default {}
   */
  slots: PropTypes.shape({
    input: PropTypes.elementType,
    mark: PropTypes.elementType,
    markLabel: PropTypes.elementType,
    rail: PropTypes.elementType,
    root: PropTypes.elementType,
    thumb: PropTypes.elementType,
    track: PropTypes.elementType,
    valueLabel: PropTypes.elementType
  }),
  /**
   * The granularity with which the slider can step through values. (A "discrete" slider.)
   * The `min` prop serves as the origin for the valid values.
   * We recommend (max - min) to be evenly divisible by the step.
   *
   * When step is `null`, the thumb can only be slid onto marks provided with the `marks` prop.
   * @default 1
   */
  step: PropTypes.number,
  /**
   * The system prop that allows defining system overrides as well as additional CSS styles.
   */
  sx: PropTypes.oneOfType([PropTypes.arrayOf(PropTypes.oneOfType([PropTypes.func, PropTypes.object, PropTypes.bool])), PropTypes.func, PropTypes.object]),
  /**
   * Tab index attribute of the hidden `input` element.
   */
  tabIndex: PropTypes.number,
  /**
   * The track presentation:
   *
   * - `normal` the track will render a bar representing the slider value.
   * - `inverted` the track will render a bar representing the remaining slider value.
   * - `false` the track will render without a bar.
   * @default 'normal'
   */
  track: PropTypes.oneOf(['inverted', 'normal', false]),
  /**
   * The value of the slider.
   * For ranged sliders, provide an array with two values.
   */
  value: PropTypes.oneOfType([PropTypes.arrayOf(PropTypes.number), PropTypes.number]),
  /**
   * Controls when the value label is displayed:
   *
   * - `auto` the value label will display when the thumb is hovered or focused.
   * - `on` will display persistently.
   * - `off` will never display.
   * @default 'off'
   */
  valueLabelDisplay: PropTypes.oneOf(['auto', 'off', 'on']),
  /**
   * The format function the value label's value.
   *
   * When a function is provided, it should have the following signature:
   *
   * - {number} value The value label's value to format
   * - {number} index The value label's index to format
   * @default (x) => x
   */
  valueLabelFormat: PropTypes.oneOfType([PropTypes.func, PropTypes.string])
} : void 0;
export default Slider;