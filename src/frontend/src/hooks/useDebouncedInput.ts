import { useCallback, useEffect, useState } from 'react';

interface IDebouncedInputProps {
  ms?: number;
  init: any;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

function debounce(func: IDebouncedInputProps['onChange'], timeout = 300) {
  let timer: any;
  return (arg: React.ChangeEvent<HTMLInputElement>) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      func(arg);
    }, timeout);
  };
}

/**
 *
 * A React hook for debouncing react synthetic events.
 *
 * Returns the value and non-debounced event handler.
 *
 * @example
 * const [value, handleChange] = useDebouncedInput({
 *   ms: 200,
 *   init: initialValue,
 *   onChange: debouncedEvent => {
 *     // do your expensive function call here
 *   },
 * });
 *
 */
export default function useDebouncedInput({ ms = 200, init, onChange = () => {} }: IDebouncedInputProps) {
  const [input, setInput] = useState(init);

  useEffect(() => setInput(init), [init]);

  const debounceEvent = useCallback(debounce(onChange, ms), []);

  const handleChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      if (event.persist) {
        event.persist();
      }
      const { name, value } = event.target;
      setInput((prev: any) => (typeof init === 'object' ? { ...prev, [name]: value } : value));
      debounceEvent(event);
    },
    [debounceEvent, init],
  );

  return [input, handleChange, setInput];
}
