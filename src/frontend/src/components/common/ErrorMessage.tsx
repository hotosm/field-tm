import React from 'react';

type propType = {
  message: string;
};

export default function ErrorMessage({ message }: propType) {
  return (
    <span role="alert" className="fmtm-text-xs fmtm-text-red-medium">
      {message}
    </span>
  );
}
