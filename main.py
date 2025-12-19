from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QStackedWidget,
    QDialog, QLabel, QPushButton, QLineEdit
)
from PyQt5.QtCore import (
    QPropertyAnimation, QRect, QParallelAnimationGroup,
    QTimer, Qt, QEvent
)
from PyQt5.QtWidgets import QGraphicsOpacityEffect
import sys
import traceback

from screens.welcome import WelcomeScreen
from screens.auth import AuthScreen
from screens.menu import MenuScreen
from screens.transaction import TransactionScreen
from screens.receipt import ReceiptScreen
from screens.admin import AdminScreen

from database.db import log_event
from security import verify_pin   # ✅ correct API


# ============================================================
#  Animated Stack
# ============================================================
class AnimatedStack(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.animation_duration = 400

    def fade_to(self, index):
        if self.width() == 0 or self.height() == 0:
            self.setCurrentIndex(index)
            return

        current = self.currentWidget()
        nxt = self.widget(index)

        fx_out = QGraphicsOpacityEffect(current)
        fx_in = QGraphicsOpacityEffect(nxt)
        current.setGraphicsEffect(fx_out)
        nxt.setGraphicsEffect(fx_in)

        fx_in.setOpacity(0)
        self.setCurrentIndex(index)

        a_out = QPropertyAnimation(fx_out, b"opacity")
        a_in = QPropertyAnimation(fx_in, b"opacity")

        for a in (a_out, a_in):
            a.setDuration(self.animation_duration)

        a_out.setStartValue(1)
        a_out.setEndValue(0)
        a_in.setStartValue(0)
        a_in.setEndValue(1)

        group = QParallelAnimationGroup(self)
        group.addAnimation(a_out)
        group.addAnimation(a_in)
        group.start()

    def slide_to(self, index, direction="left"):
        if self.width() == 0 or self.height() == 0:
            self.setCurrentIndex(index)
            return

        current = self.currentWidget()
        nxt = self.widget(index)

        w, h = self.width(), self.height()
        start_x = w if direction == "left" else -w

        nxt.setGeometry(start_x, 0, w, h)
        self.setCurrentIndex(index)

        a_cur = QPropertyAnimation(current, b"geometry")
        a_nxt = QPropertyAnimation(nxt, b"geometry")

        for a in (a_cur, a_nxt):
            a.setDuration(self.animation_duration)

        a_cur.setStartValue(QRect(0, 0, w, h))
        a_cur.setEndValue(QRect(-start_x, 0, w, h))
        a_nxt.setStartValue(QRect(start_x, 0, w, h))
        a_nxt.setEndValue(QRect(0, 0, w, h))

        group = QParallelAnimationGroup(self)
        group.addAnimation(a_cur)
        group.addAnimation(a_nxt)
        group.start()


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
#  Admin PIN Dialog (PBKDF2 – FINAL)
# ============================================================
class AdminPinDialog(QDialog):
    """
    Admin PIN = 4321
    Hash generated ONCE using:
        from security import hash_pin
        print(hash_pin("4321").hex())
    """

    # 🔐 PASTE YOUR GENERATED HEX STRING HERE
    ADMIN_PIN_HASH = "3ef6cbe5bbca5bbf8dacd20cc09f00187a419909845783e512671c6627b31c828a92e565359a9fe4e416c5e2f1faa46a"

    def __init__(self):
        super().__init__()
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        label = QLabel("Enter Admin PIN")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size:22px;")

        self.input = QLineEdit()
        self.input.setEchoMode(QLineEdit.Password)
        self.input.setMaxLength(12)
        self.input.setAlignment(Qt.AlignCenter)
        self.input.setStyleSheet("font-size:22px;")

        btn = QPushButton("Unlock")
        btn.clicked.connect(self.check)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.input)
        layout.addWidget(btn)

    def check(self):
        pin = self.input.text().strip()
        if verify_pin(pin, self.ADMIN_PIN_HASH):
            self.accept()
        else:
            self.input.clear()


# ============================================================
#  Main Window (Kiosk Mode)
# ============================================================
class MainWindow(QWidget):
    IDLE_SECONDS = 60

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nyxon Online Banking Kiosk")
        self.setStyleSheet("background-color:#f8f9fa;")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        self.stack = AnimatedStack()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        # Screens
        self.welcome = WelcomeScreen(self.go_auth)
        self.auth = AuthScreen(self.go_menu, self.go_welcome)
        self.menu = MenuScreen(self.go_transaction, self.go_welcome)
        self.transaction = TransactionScreen(self.go_receipt)
        self.receipt = ReceiptScreen(self.go_welcome)
        self.admin = AdminScreen(self.go_welcome)

        for s in (
            self.welcome, self.auth, self.menu,
            self.transaction, self.receipt, self.admin
        ):
            self.stack.addWidget(s)

        self.stack.setCurrentWidget(self.welcome)

        # Audit boot
        try:
            log_event(None, "SYSTEM_BOOT", details="Kiosk started")
        except Exception:
            traceback.print_exc()

        # Idle timer
        self.idle_timer = QTimer(self)
        self.idle_timer.setInterval(self.IDLE_SECONDS * 1000)
        self.idle_timer.timeout.connect(self._idle_trigger)
        self.idle_timer.start()

        QApplication.instance().installEventFilter(self)

    # ---------- Idle Handling ----------
    def eventFilter(self, obj, event):
        if event.type() in (
            QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.MouseButtonRelease,
            QEvent.KeyPress, QEvent.KeyRelease
        ):
            self.idle_timer.start()
        return super().eventFilter(obj, event)

    def _idle_trigger(self):
        dlg = IdleWarningDialog(seconds=10)
        countdown = QTimer(self)
        countdown.setInterval(1000)

        def tick():
            dlg.tick()
            if dlg.seconds <= 0:
                countdown.stop()
                dlg.reject()
                self.go_welcome()

        countdown.timeout.connect(tick)
        countdown.start()

        if dlg.exec_() == QDialog.Accepted:
            countdown.stop()
            self.idle_timer.start()

    # ---------- Admin Shortcut ----------
    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key_A and
            event.modifiers() & Qt.ControlModifier and
            event.modifiers() & Qt.ShiftModifier
        ):
            dlg = AdminPinDialog()
            if dlg.exec_() == QDialog.Accepted:
                log_event(None, "ADMIN_UNLOCK", details="Admin panel opened")
                self.go_admin()
            return

        if event.key() == Qt.Key_Escape:
            event.ignore()
            return

        super().keyPressEvent(event)

    # ---------- Navigation ----------
    def go_welcome(self):
        self.stack.fade_to(self.stack.indexOf(self.welcome))

    def go_auth(self):
        self.stack.slide_to(self.stack.indexOf(self.auth))

    def go_admin(self):
        self.stack.fade_to(self.stack.indexOf(self.admin))

    def go_menu(self, account_id, balance):
        self.menu.set_user(account_id, balance)
        self.stack.slide_to(self.stack.indexOf(self.menu))

    def go_transaction(self, option, account_id, balance):
        self.transaction.set_context(option, account_id, balance)
        self.stack.slide_to(self.stack.indexOf(self.transaction))

    def go_receipt(self, receipt_data):
        self.receipt.set_receipt(receipt_data)
        self.stack.fade_to(self.stack.indexOf(self.receipt))


# ============================================================
#  Boot
# ============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    QTimer.singleShot(120, window.showFullScreen)
    sys.exit(app.exec_())
