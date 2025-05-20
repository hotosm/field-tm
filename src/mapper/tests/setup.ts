// Polyfill required for .arrayBuffer() on Blob
// See: https://github.com/jsdom/jsdom/issues/2555

// import { vi } from 'vitest';
import { Blob as BlobPolyfill } from 'node:buffer';

global.Blob = BlobPolyfill as any;

// class FormDataPolyfill {
//     append = vi.fn();
// }
// global.FormData = FormDataPolyfill as any;
