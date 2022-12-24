import React from 'react';
import { WithAsProps, RsRefForwardingComponent } from '../@types/common';
export declare type ComponentProps = WithAsProps & React.HTMLAttributes<HTMLDivElement>;
interface Props extends React.HTMLAttributes<HTMLDivElement> {
    name: string;
    componentAs?: React.ElementType;
    componentClassPrefix?: string;
}
/**
 * Create a component with `classPrefix` and `as` attributes.
 */
declare function createComponent({ name, componentAs, componentClassPrefix, ...defaultProps }: Props): RsRefForwardingComponent<"div", ComponentProps>;
export default createComponent;
