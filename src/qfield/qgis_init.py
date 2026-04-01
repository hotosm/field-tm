"""QGIS application setup, processing init, and logger hook."""

import sys
import os
import logging
import atexit
from typing import Optional, Any


qgis_application = None


def setup_logging() -> logging.Logger:
    """Setup logging configuration."""
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def setup_qgis_paths() -> None:
    """Initialize QGIS paths."""
    qgis_pluginpath = os.environ.get('QGIS3_PLUGINPATH', '/usr/share/qgis/python/plugins/')
    if qgis_pluginpath not in sys.path:
        sys.path.append(qgis_pluginpath)


def start_qgis_application(
    enable_processing: bool = True,
    verbose: bool = False,
    log: Optional[logging.Logger] = None,
) -> Any:
    """
    Start QGIS application with proper error handling.

    Args:
        enable_processing: Enable processing algorithms
        verbose: Output QGIS settings
        log: Logger instance

    Returns:
        QgsApplication instance

    Raises:
        RuntimeError: If QGIS version is incompatible or initialization fails
    """
    global qgis_application

    log = log or logging.getLogger(__name__)

    if qgis_application is not None:
        log.info("QGIS application already initialized")
        return qgis_application

    # Set environment variables
    os.environ.update({
        'QGIS_NO_OVERRIDE_IMPORT': '1',
        'QGIS_DISABLE_MESSAGE_HOOKS': '1'
    })

    # Set offscreen mode if no display
    if not os.environ.get('DISPLAY'):
        log.info("Setting offscreen mode")
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'

    setup_qgis_paths()

    try:
        from qgis.core import Qgis, QgsApplication

        log.info(f"Starting QGIS application: {Qgis.QGIS_VERSION}")

        # Initialise
        qgis_prefix = os.environ.get('QGIS3_HOME', '/usr')
        os.environ['QGIS_PREFIX_PATH'] = qgis_prefix
        qgis_application = QgsApplication([], False)
        qgis_application.setPrefixPath(qgis_prefix, True)
        qgis_application.initQgis()

        # Register cleanup (else may prevent container shutdown)
        @atexit.register
        def cleanup_qgis():
            global qgis_application
            if qgis_application:
                log.info("Cleaning up QGIS application")
                qgis_application.exitQgis()
                qgis_application = None

        # Install message logger
        install_logger_hook(qgis_application, log)

        if verbose:
            print(qgis_application.showSettings())

        # Initialize processing
        if enable_processing:
            init_processing(log)

        log.info("QGIS application initialized successfully")
        return qgis_application

    except ImportError as e:
        raise RuntimeError(f"Failed to import QGIS modules: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize QGIS: {e}")


def init_processing(log: logging.Logger) -> None:
    """Initialize QGIS processing algorithms."""
    try:
        from processing.core.Processing import Processing
        from qgis.analysis import QgsNativeAlgorithms

        # Add native algorithms
        qgis_application.processingRegistry().addProvider(QgsNativeAlgorithms())
        Processing.initialize()

        log.info("QGIS processing initialized")

    except Exception as e:
        log.error(f"Failed to initialize processing: {e}")
        raise


def install_logger_hook(qgis_app: Any, log: logging.Logger) -> None:
    """Install QGIS message log hook."""
    try:
        from qgis.core import Qgis

        def log_qgis_message(message: str, tag: str, level: int):
            msg = f"QGIS {tag}: {message}"
            if level == Qgis.Warning:
                log.warning(msg)
            elif level == Qgis.Critical:
                log.error(msg)
            else:
                log.debug(msg)

        qgis_app.messageLog().messageReceived.connect(log_qgis_message)

    except Exception as e:
        log.warning(f"Failed to install logger hook: {e}")
