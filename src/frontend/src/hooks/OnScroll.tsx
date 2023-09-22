import React, { useEffect, useState } from 'react';

export default function OnScroll(element, dep) {
  const [scrollTop, setScrollTop] = useState(0);
  useEffect(() => {
    const doc = document.getElementsByClassName('mainview')[0];

    const handleScroll = (event) => {
      if (element != undefined) {
        setScrollTop(element.getTargetElement().getBoundingClientRect().y);
      }
    };

    doc.addEventListener('scroll', handleScroll);
    window.addEventListener('resize', handleScroll);

    return () => {
      doc.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleScroll);
    };
  }, [element, dep]);

  return { y: scrollTop };
}
