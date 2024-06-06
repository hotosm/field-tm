/* eslint-disable no-nested-ternary */
/* eslint-disable react/jsx-props-no-spreading */
/* eslint-disable react/jsx-no-useless-fragment */
import React from 'react';
import '../map.scss';

const { Children, cloneElement } = React;

const MapContainer = ({ children, mapInstance = null, ref, ...rest }) => {
  const childrenCount = Children.count(children);
  const props = {
    map: mapInstance,
  };
  return (
    <div ref={ref} id="ol-map" className="ol-map" {...rest}>
      {childrenCount < 1 ? (
        <></>
      ) : childrenCount > 1 ? (
        Children.map(children, (child) => (child ? cloneElement(child, { ...props, ref: null }) : <></>))
      ) : (
        cloneElement(children, { ...props, ref: null })
      )}
    </div>
  );
};

// TODO replace with typescript
// MapContainer.propTypes = {
//   children: PropTypes.node.isRequired,
//   mapInstance: PropTypes.oneOfType([PropTypes.object, PropTypes.number]),
// };

MapContainer.displayName = 'MapContainer';

export default MapContainer;
