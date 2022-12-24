import * as PropTypes from 'prop-types';
export default function deprecatePropType<T extends PropTypes.Validator<any>>(propType: T, explanation?: string): typeof propType;
