import React from 'react';
import { Loader2 } from 'lucide-react';

export type variantType =
  | 'primary-red'
  | 'secondary-red'
  | 'link-red'
  | 'primary-grey'
  | 'secondary-grey'
  | 'link-grey';

interface IButton {
  variant: variantType;
  children?: React.ReactNode;
  type?: 'submit' | 'button';
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  className?: string;
  isLoading?: boolean;
  disabled?: boolean;
  btnId?: string;
  btnTestId?: string;
  ref?: React.Ref<HTMLButtonElement> | null;
  shouldFocus?: boolean;
}

const variantStyle = {
  primary: 'fmtm-py-2 fmtm-px-4 fmtm-gap-2 fmtm-rounded',
  secondary: 'fmtm-py-2 fmtm-px-4 fmtm-gap-2 fmtm-rounded fmtm-border',
  link: 'fmtm-py-2 fmtm-px-1 fmtm-gap-2 ',
};

const btnStyle = (variant: variantType) => {
  switch (variant) {
    case 'primary-red':
      return `${variantStyle.primary} fmtm-bg-red-medium fmtm-text-white hover:fmtm-bg-red-dark disabled:fmtm-bg-red-400`;
    case 'secondary-red':
      return `${variantStyle.secondary} fmtm-bg-white fmtm-text-red-medium fmtm-border-red-medium hover:fmtm-text-red-dark hover:fmtm-border-red-dark hover:fmtm-bg-red-light disabled:fmtm-text-red-400 disabled:fmtm-border-red-400 disabled:fmtm-bg-white`;
    case 'link-red':
      return `${variantStyle.link} fmtm-text-red-medium hover:fmtm-text-red-dark disabled:fmtm-text-red-400`;
    case 'primary-grey':
      return `${variantStyle.primary} fmtm-bg-grey-800 fmtm-text-white hover:fmtm-bg-grey-900 disabled:fmtm-bg-grey-600`;
    case 'secondary-grey':
      return `${variantStyle.secondary} fmtm-bg-white fmtm-text-grey-800 fmtm-border-grey-800 hover:fmtm-text-grey-900 hover:fmtm-border-grey-900 hover:fmtm-bg-grey-50 disabled:fmtm-text-grey-600 disabled:fmtm-border-grey-600 disabled:fmtm-bg-white`;
    case 'link-grey':
      return `${variantStyle.link} fmtm-text-grey-800 hover:fmtm-text-grey-900 disabled:fmtm-text-grey-600`;
  }
};

const Button = ({
  variant,
  type = 'button',
  onClick,
  disabled,
  className,
  isLoading,
  btnId,
  btnTestId,
  children,
  ref,
  shouldFocus = false,
}: IButton) => (
  <button
    ref={ref}
    data-btnid={btnId}
    data-testid={btnTestId}
    type={type}
    onClick={onClick}
    className={`fmtm-button fmtm-group fmtm-flex fmtm-justify-center fmtm-items-center fmtm-gap-2 fmtm-outline-none fmtm-w-fit fmtm-duration-200 fmtm-whitespace-nowrap ${shouldFocus && 'focus:fmtm-border-[#D73F37] focus:fmtm-ring-[#D73F37]/50 focus:fmtm-ring-[3px]'} ${btnStyle(variant)} ${className} ${(disabled || isLoading) && 'fmtm-cursor-not-allowed'}`}
    disabled={disabled || isLoading}
  >
    <>
      {children}
      {isLoading && <Loader2 className="fmtm-animate-spin fmtm-w-4" strokeWidth={3.25} />}
    </>
  </button>
);

export default Button;
