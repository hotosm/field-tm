import { useRef, useEffect } from 'react';

function useDocumentTitle(titleSuffix: string, prevailOnUnmount: boolean = false) {
  const defaultTitle = useRef(document.title);

  useEffect(() => {
    document.title = `${titleSuffix} - HOT Field Tasking Manager`;
  }, [titleSuffix]);

  useEffect(
    () => () => {
      if (!prevailOnUnmount) {
        document.title = defaultTitle.current;
      }
    },
    [],
  );
}

export default useDocumentTitle;
