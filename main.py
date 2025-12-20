from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QStackedWidget,
    QDialog, QLabel, QPushButton, QLineEdit
)
from PyQt5.QtCore import QTimer, Qt, QEvent
import sys
import traceback

# Screens
from screens.welcome import WelcomeScreen
from screens.auth import AuthScreen
from screens.menu import MenuScreen
from screens.transaction import TransactionScreen
from screens.receipt import ReceiptScreen
from screens.admin import AdminScreen
from screens.account_info import AccountInfoScreen
from screens.history import TransactionHistoryScreen

from database.db import log_event
from security import verify_pin


# ============================================================
#  Idle Warning Dialog
# ============================================================
class IdleWarningDialog(QDialog):
    def __init__(self, seconds=10):
        super().__init__()
        self.seconds = seconds
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        self.label = QLabel(self._text())
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size:26px;font-weight:bold;")

        btn = QPushButton("Continue Session")
        btn.setFixedHeight(50)
        btn.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(btn)

    def _text(self):
        return f"Session will reset in {self.seconds} seconds"

    def tick(self):
        self.seconds -= 1
        self.label.setText(self._text())


# ============================================================
#  Admin PIN Dialog
# ============================================================
class AdminPinDialog(QDialog):
    ADMIN_PIN_HASH = (
        "3ef6cbe5bbca5bbf8dacd20cc09f0018"
        "7a419909845783e512671c6627b31c82"
        "8a92e565359a9fe4e416c5e2f1faa46a"
    )

    def __init__(self):
        super().__init__()
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        label = QLabel("Enter Admin PIN")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size:22px;")

        self.input = QLineEdit()
        self.input.setEchoMode(QLineEdit.Password)
        self.input.setAlignment(Qt.AlignCenter)
        self.input.setStyleSheet("font-size:22px;")

        btn = QPushButton("Unlock")
        btn.clicked.connect(self.check)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.input)
        layout.addWidget(btn)

    def check(self):
        if verify_pin(self.input.text(), self.ADMIN_PIN_HASH):
            self.accept()
        else:
            self.input.clear()


# ============================================================
#  Main Window (ATM / KIOSK SAFE)
# ============================================================
class MainWindow(QWidget):
    IDLE_SECONDS = 60

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nyxon Online Banking Kiosk")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setStyleSheet("background-color:#f8f9fa;")

        # ---------- STACK ----------
        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        # ---------- Screens ----------
        self.welcome = WelcomeScreen(self.go_auth)
        self.auth = AuthScreen(self.go_menu, self.go_welcome)
        self.menu = MenuScreen(self.go_transaction, self.go_welcome)

        self.transaction = TransactionScreen(
            self.go_receipt,
            self.go_home
        )

        self.receipt = ReceiptScreen(self.go_home)
        self.account_info = AccountInfoScreen(self.go_home)
        self.history = TransactionHistoryScreen(self.go_home)
        self.admin = AdminScreen(self.go_welcome)

        for screen in (
            self.welcome,
            self.auth,
            self.menu,
            self.transaction,
            self.receipt,
            self.account_info,
            self.history,
            self.admin
        ):
            self.stack.addWidget(screen)

        self.stack.setCurrentWidget(self.welcome)

        # ---------- Audit ----------
        try:
            log_event(None, "SYSTEM_BOOT", details="Kiosk started")
        except Exception:
            traceback.print_exc()

        # ---------- Idle Timer ----------
        self.idle_timer = QTimer(self)
        self.idle_timer.setInterval(self.IDLE_SECONDS * 1000)
        self.idle_timer.timeout.connect(self._idle_trigger)
        self.idle_timer.start()

        QApplication.instance().installEventFilter(self)

    # ========================================================
    #  HARD SESSION RESET (MOST IMPORTANT FIX)
    # ========================================================
    def reset_session(self):
        """
        Fully resets the kiosk session.
        This PREVENTS white screens.
        """
        self.menu.account_id = None
        self.menu.balance = None

        for screen in (
            self.transaction,
            self.history,
            self.account_info,
            self.receipt
        ):
            try:
                screen.reset()
            except Exception:
                pass

    # ========================================================
    #  Navigation
    # ========================================================
    def go_home(self):
        self.reset_session()
        self.stack.setCurrentWidget(self.welcome)

    def go_welcome(self):
        self.reset_session()
        self.stack.setCurrentWidget(self.welcome)

    def go_auth(self):
        self.stack.setCurrentWidget(self.auth)

    def go_menu(self, account_id, balance):
        self.menu.set_user(account_id, balance)
        self.stack.setCurrentWidget(self.menu)

    def go_transaction(self, option, account_id, balance):
        if option == "info":
            self.account_info.reset()
            self.account_info.set_account(account_id)
            self.stack.setCurrentWidget(self.account_info)
            return

        if option == "statement":
            self.history.reset()
            self.history.set_account(account_id)
            self.stack.setCurrentWidget(self.history)
            return

        self.transaction.reset()
        self.transaction.set_context(option, account_id, balance)
        self.stack.setCurrentWidget(self.transaction)

    def go_receipt(self, receipt_data):
        self.receipt.reset()
        self.receipt.set_receipt(receipt_data)
        self.stack.setCurrentWidget(self.receipt)

    def go_admin(self):
        self.stack.setCurrentWidget(self.admin)

    # ========================================================
    #  Idle Handling
    # ========================================================
    def eventFilter(self, obj, event):
        if event.type() in (
            QEvent.MouseMove,
            QEvent.MouseButtonPress,
            QEvent.KeyPress,
            QEvent.KeyRelease
        ):
            self.idle_timer.start()
        return super().eventFilter(obj, event)

    def _idle_trigger(self):
        dlg = IdleWarningDialog(10)
        timer = QTimer(self)

        def tick():
            dlg.tick()
            if dlg.seconds <= 0:
                timer.stop()
                dlg.reject()
                self.reset_session()
                self.stack.setCurrentWidget(self.welcome)

        timer.timeout.connect(tick)
        timer.start(1000)

        if dlg.exec_():
            timer.stop()
            self.idle_timer.start()

    # ========================================================
    #  Admin Shortcut
    # ========================================================
    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key_A and
            event.modifiers() & Qt.ControlModifier and
            event.modifiers() & Qt.ShiftModifier
        ):
            if AdminPinDialog().exec_():
                try:
                    log_event(None, "ADMIN_UNLOCK")
                except Exception:
                    traceback.print_exc()
                self.go_admin()
            return

        if event.key() == Qt.Key_Escape:
            event.ignore()
            return

        super().keyPressEvent(event)


# ============================================================
#  Boot
# ============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    QTimer.singleShot(100, window.showFullScreen)
    sys.exit(app.exec_())
