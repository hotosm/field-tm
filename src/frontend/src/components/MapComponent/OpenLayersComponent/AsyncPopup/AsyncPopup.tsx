import React, { useEffect, useRef, useState, useCallback } from 'react';
import { renderToString } from 'react-dom/server';
import Overlay from 'ol/Overlay';
import { getCenter } from 'ol/extent';
import './asyncpopup.scss';

type asyncPopupPropType = {
  map: any;
  fetchPopupData?: any;
  popupUI: any;
  openPopupFor?: () => void;
  zoomedExtent?: any;
  onPopupClose?: () => void;
  closePopup?: any;
  loading?: boolean;
  showOnHover?: string;
  primaryKey?: string;
  popupId?: string;
  className?: string;
};

function hasKey(obj, key) {
  return Object.keys(obj).some((item) => item === key);
}

const layerIds = ['code'];

const AsyncPopup = ({
  map,
  fetchPopupData,
  popupUI,
  openPopupFor,
  zoomedExtent,
  onPopupClose,
  closePopup = false,
  loading = false,
  showOnHover = 'click',
  primaryKey = 'uid',
  popupId = 'popupx',
  className,
}: asyncPopupPropType) => {
  const popupRef = useRef<any>(null);
  const popupCloserRef = useRef<any>(null);
  const [coordinates, setCoordinates] = useState<any>(null);
  const [overlay, setOverlay] = useState<any>(null);
  const [properties, setProperties] = useState(null);
  const [popupHTML, setPopupHTML] = useState<HTMLBodyElement | string>('');

  // add overlay to popupRef
  useEffect(() => {
    if (!map || !popupRef.current) return;
    const overlayInstance = new Overlay({
      element: popupRef.current,
      positioning: 'center-center',
      id: popupId,
      autoPan: {
        animation: {
          duration: 250,
        },
      },
    });
    setOverlay(overlayInstance);
  }, [map, popupRef]);

  // function for closing popup
  const closePopupFn = useCallback(() => {
    if (!popupCloserRef.current || !overlay) return;
    overlay.setPosition(undefined);
    setPopupHTML('');
    setProperties(null);
    if (popupCloserRef?.current instanceof HTMLElement) {
      popupCloserRef.current.blur();
    }
  }, [overlay, popupCloserRef]);

  useEffect(() => {
    if (!map || !closePopup) return;
    closePopupFn();
  }, [map, closePopup, closePopupFn]);

  useEffect(() => {
    /**
     * Alert if clicked on outside of element
     */
    function handleClickOutside(event) {
      if (popupRef.current && !popupRef?.current?.contains(event.target)) {
        // alert('You clicked outside of me!');
        overlay.setPosition(undefined);
        setPopupHTML('');
        setProperties(null);
        if (popupCloserRef?.current instanceof HTMLElement) {
          popupCloserRef?.current.blur();
        }
      }
    }
    // Bind the event listener
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      // Unbind the event listener on clean up
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [overlay]);
  // get properties and coordinates of feature
  useEffect(() => {
    if (!map) return;
    if (!overlay) return;

    map.on(showOnHover, (evt) => {
      overlay.setPosition(undefined);
      setPopupHTML('');
      setProperties(null);
      if (popupCloserRef?.current instanceof HTMLElement) {
        popupCloserRef.current?.blur();
      }
      const { coordinate } = evt;
      const features = map.getFeaturesAtPixel(evt.pixel);
      if (features.length < 1) {
        closePopupFn();
        return;
      }

      // in the case of cluster-layer, the features are nested within features
      const featureProperties = features[0]?.getProperties()?.features
        ? features[0]?.getProperties()?.features[0]?.getProperties()
        : features[0]?.getProperties();

      const { [primaryKey]: primaryKeyValue } = featureProperties;
      if (
        layerIds.includes(primaryKeyValue) ||
        (hasKey(featureProperties, primaryKey) && featureProperties?.[primaryKey])
      ) {
        setProperties(featureProperties);
        setCoordinates(coordinate);
      } else {
        closePopupFn();
        setProperties(null);
        setCoordinates(null);
      }
    });
  }, [map, closePopupFn, showOnHover]);

  // fetch popup data when properties is set
  useEffect(() => {
    if (!map || !properties) return;
    const { layerId } = properties;
    if (layerIds.includes(layerId) || hasKey(properties, 'layer')) {
      fetchPopupData(properties);
    }
    // eslint-disable-next-line
  }, [map, properties]);

  useEffect(() => {
    if (!map || !coordinates || !overlay || !properties || closePopup) return;
    const htmlString = renderToString(popupUI(properties));
    if (!htmlString) return;
    setPopupHTML(htmlString);

    overlay.setPosition([coordinates[0], coordinates[1]]);
    const popupOverlay = map.getOverlayById(popupId);
    if (!popupOverlay) {
      map.addOverlay(overlay);
    }
  }, [map, overlay, coordinates, popupUI, properties, closePopup]);

  //   useEffect(() => {
  //     if (!map || !openPopupFor || !zoomedExtent) return;
  //     const center = getCenter(zoomedExtent);
  //     setProperties({ id: openPopupFor, layer: 'site' });
  //     setCoordinates(center);
  //   }, [map, openPopupFor, zoomedExtent]);

  return (
    <div
      ref={popupRef}
      id="popup"
      className={`ol-popup ${className}`}
      style={{ zIndex: 100009 }}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) {
          // Not triggered when swapping focus between children
          closePopupFn();
        }
      }}
    >
      <button
        ref={popupCloserRef}
        id="popup-closer"
        className="ol-popup-closer"
        type="button"
        onClick={closePopupFn}
        onKeyDown={closePopupFn}
      />
      <div id="popup-content" dangerouslySetInnerHTML={{ __html: popupHTML }} />
    </div>
  );
};

export default AsyncPopup;
