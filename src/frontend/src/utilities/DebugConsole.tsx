import React, { useEffect, useState } from 'react';

type DebugConsolePropsType = {
  showDebugConsole: boolean;
  setShowDebugConsole: (showStatus: boolean) => void;
};

const DebugConsole = ({ showDebugConsole, setShowDebugConsole }: DebugConsolePropsType) => {
  const [logs, setLogs] = useState([]);
  useEffect(() => {
    if (import.meta.env.MODE === 'development') {
      // Override console.log to capture logs
      const originalConsoleLog = console.log;
      console.log = (...args) => {
        originalConsoleLog.apply(console, args);
        setLogs((prevLogs) => [
          ...prevLogs,
          args.map((arg) => (typeof arg === 'object' ? JSON.stringify(arg) : arg)).join(' '),
        ]);
      };

      // Restore original console.log when component unmounts
      return () => {
        console.log = originalConsoleLog;
      };
    }
  }, []);

  return (
    <div>
      {import.meta.env.MODE === 'development' && (
        <div>
          <div
            className={`fmtm-fixed fmtm-bottom-0 fmtm-w-full fmtm-h-[33vh] fmtm-bg-white fmtm-border fmtm-px-4 fmtm-py-8 fmtm-flex-col fmtm-z-[1000] fmtm-overflow-y-auto ${
              showDebugConsole ? '!fmtm-flex' : '!fmtm-hidden'
            }`}
          >
            <button style={{ alignSelf: 'flex-end', marginBottom: '10px' }} onClick={() => setShowDebugConsole(false)}>
              Close
            </button>
            {logs.map((log, index) => (
              <p key={index}>{log}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DebugConsole;
