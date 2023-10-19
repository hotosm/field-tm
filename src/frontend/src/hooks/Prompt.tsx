import React from 'react';
import pathNotToBlock from '../constants/blockerUrl';
import { unstable_useBlocker as useBlocker } from 'react-router-dom';

function Prompt(props) {
  const block = props.when;
  useBlocker(({ nextLocation }) => {
    console.log(nextLocation, 'next');
    if (block && !pathNotToBlock.includes(nextLocation.pathname)) {
      return !window.confirm(props.message);
    }
    return false;
  });

  return <div key={block} />;
}

export default Prompt;
