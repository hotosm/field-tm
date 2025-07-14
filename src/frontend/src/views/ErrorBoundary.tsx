import React from 'react';
import SomethingWentWrongImage from '@/assets/images/something_went_wrong.png';
import Button from '@/components/common/Button';
import AssetModules from '@/shared/AssetModules';

interface ErrorBoundaryProps {
  showError?: boolean;
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
  errorInfo: object | null | any;
  showDetails: boolean;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { error: null, errorInfo: null, showDetails: false };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo,
      showDetails: false,
    });
  }

  render() {
    const { errorInfo, error, showDetails } = this.state;

    const { children } = this.props;
    if (errorInfo) {
      return (
        <div className="md:fmtm-px-[2rem] lg:fmtm-px-[4.5rem]">
          <div className="fmtm-flex fmtm-flex-col fmtm-items-center fmtm-justify-center fmtm-gap-5 fmtm-mt-[5rem]">
            <div>
              <img src={SomethingWentWrongImage} alt="Something Went Wrong Photo" />
            </div>
            <div className="fmtm-flex fmtm-flex-col fmtm-gap-5">
              <h2 className="fmtm-text-[1.5rem] md:fmtm-text-[2rem] lg:fmtm-text-[2.5rem] fmtm-text-primaryRed fmtm-font-primary fmtm-font-bold fmtm-text-center">
                OH NO, SOMETHING WENT WRONG!!
              </h2>
              <p className="fmtm-text-sm sm:fmtm-text-base fmtm-font-extralight fmtm-text-center fmtm-text-[#68707F]">
                We encountered an error. We are trying to fix the problem, it might take a few second.
              </p>
              <div className="fmtm-flex fmtm-items-center fmtm-gap-5 fmtm-justify-center">
                <Button variant="secondary-red" onClick={() => window.location.reload()}>
                  Reload
                </Button>
                <Button
                  variant="secondary-red"
                  onClick={() =>
                    this.setState({
                      error,
                      errorInfo,
                      showDetails: !this.state.showDetails,
                    })
                  }
                  className="fmtm-border-none"
                >
                  View Details
                  <AssetModules.KeyboardArrowUpIcon className={`${this.state.showDetails ? 'fmtm-rotate-180' : ''}`} />
                </Button>
              </div>
            </div>
          </div>
          {showDetails && (
            <div className="fmtm-max-w-[39rem] fmtm-flex fmtm-flex-col fmtm-mx-auto fmtm-gap-3 fmtm-p-6 fmtm-bg-red-50 fmtm-text-primaryRed fmtm-my-3 fmtm-border-[1px] fmtm-rounded-lg fmtm-text-sm sm:fmtm-text-base">
              <p className="fmtm-break-words">{error && error.toString()}</p>
              <p className="fmtm-break-words">{errorInfo.componentStack}</p>
            </div>
          )}
        </div>
      );
    }

    return children;
  }
}

export default ErrorBoundary;
