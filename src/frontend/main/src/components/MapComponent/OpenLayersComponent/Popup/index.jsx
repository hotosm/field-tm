/* eslint-disable react/prop-types */
/* eslint-disable jsx-a11y/anchor-has-content */
/* eslint-disable func-names */
/* eslint-disable jsx-a11y/control-has-associated-label */
import React, { useEffect } from 'react';
import Overlay from 'ol/Overlay';
import './popup.scss';

const Popup = ({ map, except }) => {
  useEffect(() => {
    if (!map) return;

    const container = document.getElementById('popup');
    const content = document.getElementById('popup-content');
    const closer = document.getElementById('popup-closer');

    const overlay = new Overlay({
      element: container,
      autoPan: true,
      autoPanAnimation: {
        duration: 250,
      },
    });

    closer.onclick = function () {
      overlay.setPosition(undefined);
      closer.blur();
      return false;
    };

    map.on('singleclick', (evt) => {
      const { coordinate } = evt;
      const features = map.getFeaturesAtPixel(evt.pixel);
      if (features.length < 1) {
        overlay.setPosition(undefined);
        closer.blur();
        content.innerHTML = '';
        return;
      }
      const properties = features[0].getProperties();
      const { layerId } = properties;
      if (layerId === except) {
        overlay.setPosition(undefined);
        closer.blur();
        return;
      }
      content.innerHTML = `<table style="width:100%;border-collapse:unset;">
        ${Object.keys(properties).reduce(
          (str, key) =>
            `${str}
          <tr>
            <td>${key}</td>
            <td><b>${properties[key]}</b>
            </td>
          </tr>`,
          '',
        )}
      </table>`;
      overlay.setPosition(coordinate);
      map.addOverlay(overlay);
    });
  }, [map]);

  return (
    <div id="popup" className="ol-popup">
      <a href={() => {}} id="popup-closer" className="ol-popup-closer" />
      <div id="popup-content" className="is-overflow" />
    </div>
  );
};

export default Popup;
