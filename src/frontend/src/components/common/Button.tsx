import { Loader2 } from 'lucide-react';
import React from 'react';

interface IButton {
  btnText: string;
  btnType: 'primary' | 'secondary' | 'other' | 'disabled';
  type?: 'submit' | 'button';
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  className?: string;
  count?: number;
  dataTip?: string;
  icon?: React.ReactNode;
  isLoading?: boolean;
  disabled?: boolean;
  loadingText?: string;
  btnId?: string;
  btnTestId?: string;
}

const btnStyle = (btnType, className) => {
  switch (btnType) {
    case 'primary':
      return `${className} hover:fmtm-bg-red-700 fmtm-flex fmtm-px-4 fmtm-py-1 fmtm-bg-primaryRed fmtm-text-white fmtm-rounded-[8px] fmtm-w-fit`;
    case 'secondary':
      return `hover:fmtm-bg-gray-100 fmtm-flex fmtm-bg-white  fmtm-px-4 fmtm-py-1 fmtm-border border-[#E0E0E0] fmtm-rounded-[8px] fmtm-w-fit ${className}`;

    case 'other':
      return `fmtm-py-1 fmtm-px-4 fmtm-text-red-600 fmtm-rounded-lg fmtm-border-[1px] fmtm-border-red-600 hover:fmtm-text-red-700 hover:fmtm-border-red-700 fmtm-w-fit ${className}`;
    case 'disabled':
      return `fmtm-py-1 fmtm-px-4 fmtm-text-white fmtm-rounded-lg fmtm-bg-gray-400 fmtm-cursor-not-allowed fmtm-w-fit ${className}`;

    default:
      return 'fmtm-primary';
  }
};
const Button = ({
  btnText,
  btnType,
  type,
  onClick,
  disabled,
  className,
  count,
  dataTip,
  icon,
  isLoading,
  loadingText,
  btnId,
  btnTestId,
}: IButton) => (
  <div>
    <button
      data-btnid={btnId}
      data-testid={btnTestId}
      type={type === 'submit' ? 'submit' : 'button'}
      onClick={onClick}
      className={`fmtm-text-lg fmtm-group fmtm-flex fmtm-items-center fmtm-gap-2 fmtm-outline-none ${btnStyle(
        isLoading || disabled ? 'disabled' : btnType,
        className,
      )}`}
      disabled={disabled || isLoading}
      title={dataTip}
    >
      {isLoading ? (
        <>
          {loadingText ? loadingText : type === 'submit' ? 'Submitting...' : 'Loading...'}
          <Loader2 className="fmtm-mr-2 fmtm-h-6 fmtm-w-6 fmtm-animate-spin" />
        </>
      ) : (
        <>
          <p className="fmtm-whitespace-nowrap">{btnText}</p>
          {count && (
            <p className="fmtm-flex fmtm-justify-center fmtm-items-center fmtm-text-overline fmtm-ml-2 fmtm-rounded-[40px] fmtm-bg-active_text fmtm-text-white fmtm-w-6 fmtm-h-6">
              {count}
            </p>
          )}
          {icon && <div>{icon}</div>}
        </>
      )}
    </button>
  </div>
);

export default Button;
