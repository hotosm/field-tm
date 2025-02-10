import React from 'react';

declare module '*.png';
declare module '*.svg';
declare module 'ol/style';
declare module 'pako/lib/deflate';
declare module 'react' {
  namespace JSX {
    interface IntrinsicElements extends IntrinsicElements {
      'hot-tracking': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
        'site-id'?: string;
        domain?: string;
        force?: boolean;
      };
    }
  }
}
