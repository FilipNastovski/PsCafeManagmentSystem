import sys
import os
import logging
from logging.handlers import RotatingFileHandler

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QLockFile, QStandardPaths

from db import init_database, close_connection
from services import SessionService
from ui.main_window import MainWindow
from utils.app_path import get_data_path

log_file = get_data_path("pscafe.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def setup_application():
    app = QApplication(sys.argv)
    app.setApplicationName("PS Management")
    app.setOrganizationName("PsCafe")
    app.setOrganizationDomain("localhost")
    app.setStyle("Fusion")
    return app


def main():
    logger.info("Starting PlayStation Management System")
    app = setup_application()

    # Single-instance lock
    lock_path = os.path.join(
        QStandardPaths.writableLocation(QStandardPaths.TempLocation),
        "pscafe.lock"
    )
    lock = QLockFile(lock_path)

    if not lock.tryLock(100):
        pid, hostname, appname = lock.getLockInfo()  # ← get info about the locking process
        QMessageBox.warning(
            None,
            "Already Running",
            "PS Café Management is already running.\nPlease use the existing instance."
        )
        logger.warning(f"Another instance is already running. Exiting.")
        return 1

    try:
        init_database()
        logger.info("Database initialized")

        SessionService.recover_active_sessions()
        logger.info("Recovered active sessions")

        window = MainWindow()
        window.show()

        logger.info("Application window shown")
        exit_code = app.exec()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    finally:
        lock.unlock()  # Release lock on exit
        logger.info("Cleaning up resources")
        try:
            close_connection()
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
        logger.info("PlayStation Management System closed")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())