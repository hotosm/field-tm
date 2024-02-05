import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * A React custom hook that handles click events outside a specific DOM element.
 *
 * Returns a ref, toggle state and a function to handle toggle state.
 *
 * @usage
 * Put the ref on the element.
 * Toggle state to change the display from none to block or vice-versa.
 * Toggle handler on the element to trigger the toggle.
 *
 */
const useOutsideClick = (type = 'single') => {
  const ref: any = useRef();
  const [toggle, setToggle] = useState<boolean>(false);
  const onOutsideClick = useCallback((e) => {
    if (!ref.current.contains(e.target)) {
      setToggle(false);
    }
  }, []);

  useEffect(() => {
    if (toggle) {
      window.addEventListener('click', onOutsideClick);
    } else {
      window.removeEventListener('click', onOutsideClick);
    }

    return () => {
      window.removeEventListener('click', onOutsideClick);
    };
  }, [toggle, onOutsideClick]);

  const handleToggle = (): void => {
    if (type === 'multiple') {
      setToggle(true);
    } else {
      setToggle((prev) => !prev);
    }
  };

  return [ref, toggle, handleToggle];
};

export default useOutsideClick;
