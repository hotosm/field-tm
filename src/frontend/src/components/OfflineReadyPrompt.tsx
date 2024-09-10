import React, { useEffect } from 'react';
import '@/styles/OfflineReadyPrompt.css';

import { useRegisterSW } from 'virtual:pwa-register/react';
import { pwaInfo } from 'virtual:pwa-info';

console.log(pwaInfo);

function OfflineReadyPrompt() {
  // replaced dynamically
  const buildDate = '__DATE__';

  const {
    offlineReady: [offlineReady, setOfflineReady],
  } = useRegisterSW({
    onRegisteredSW(swUrl, swRegistration) {
      console.log(`Service Worker at: ${swUrl}`);
      console.log('SW Registered: ', swRegistration);
    },
    onRegisterError(error) {
      console.log('SW registration error', error);
    },
  });

  const close = () => {
    setOfflineReady(false);
  };

  useEffect(() => {
    console.log('offlineReady:', offlineReady); // Log offlineReady value
  }, [offlineReady]);

  return (
    <>
      {offlineReady && (
        <div className="OfflineReadyPrompt-container">
          <div className="OfflineReadyPrompt-toast">
            <div className="OfflineReadyPrompt-message">
              <span>App ready to work offline</span>
            </div>
            <button className="OfflineReadyPrompt-toast-button" onClick={() => close()}>
              Close
            </button>
          </div>
          <div className="OfflineReadyPrompt-date">{buildDate}</div>
        </div>
      )}
    </>
  );
}

export default OfflineReadyPrompt;
