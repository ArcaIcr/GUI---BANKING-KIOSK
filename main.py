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
#  Animated Stack (safe + anti-white-screen)
# ============================================================
class AnimatedStack(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.animation_duration = 400
        self._anim_group = None  # keep reference to avoid GC

    def _stop_anim(self):
        if self._anim_group is not None:
            try:
                self._anim_group.stop()
            except Exception:
                pass
            self._anim_group = None

    # ✅ Instant switch for dynamic/reused screens (kiosk-safe)
    def instant_to(self, index: int):
        self._stop_anim()
        self.setCurrentIndex(index)

    def fade_to(self, index: int):
        if self.width() == 0 or self.height() == 0:
            self.setCurrentIndex(index)
            return

        self._stop_anim()

        current = self.currentWidget()
        nxt = self.widget(index)

        fx_out = QGraphicsOpacityEffect(current)
        fx_in = QGraphicsOpacityEffect(nxt)
        current.setGraphicsEffect(fx_out)
        nxt.setGraphicsEffect(fx_in)

        fx_in.setOpacity(0)
        self.setCurrentIndex(index)

        a_out = QPropertyAnimation(fx_out, b"opacity", self)
        a_in = QPropertyAnimation(fx_in, b"opacity", self)

        for a in (a_out, a_in):
            a.setDuration(self.animation_duration)

        a_out.setStartValue(1)
        a_out.setEndValue(0)
        a_in.setStartValue(0)
        a_in.setEndValue(1)

        group = QParallelAnimationGroup(self)
        group.addAnimation(a_out)
        group.addAnimation(a_in)

        self._anim_group = group
        group.finished.connect(lambda: setattr(self, "_anim_group", None))
        group.start()

    def slide_to(self, index: int):
        if self.width() == 0 or self.height() == 0:
            self.setCurrentIndex(index)
            return

        self._stop_anim()

        current = self.currentWidget()
        nxt = self.widget(index)

        w, h = self.width(), self.height()

        # start next off-screen right
        nxt.setGeometry(w, 0, w, h)
        self.setCurrentIndex(index)

        a_cur = QPropertyAnimation(current, b"geometry", self)
        a_nxt = QPropertyAnimation(nxt, b"geometry", self)

        for a in (a_cur, a_nxt):
            a.setDuration(self.animation_duration)

        a_cur.setStartValue(QRect(0, 0, w, h))
        a_cur.setEndValue(QRect(-w, 0, w, h))
        a_nxt.setStartValue(QRect(w, 0, w, h))
        a_nxt.setEndValue(QRect(0, 0, w, h))

        group = QParallelAnimationGroup(self)
        group.addAnimation(a_cur)
        group.addAnimation(a_nxt)

        self._anim_group = group
        group.finished.connect(lambda: setattr(self, "_anim_group", None))
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
#  Main Window (Kiosk Controller)
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

        self.transaction = TransactionScreen(
                self.go_receipt,
                self.go_home      # ← cancel goes back to menu
            )

        self.receipt = ReceiptScreen(self.go_home)

        self.account_info = AccountInfoScreen(self.go_home)
        self.history = TransactionHistoryScreen(self.go_home)

        self.admin = AdminScreen(self.go_welcome)

        for s in (
            self.welcome, self.auth, self.menu,
            self.transaction, self.receipt,
            self.account_info, self.history,
            self.admin
        ):
            self.stack.addWidget(s)

        self.stack.setCurrentWidget(self.welcome)

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

    # ---------- Session Home ----------
    def go_home(self):
        # ✅ Use instant switch for stability (prevents white screen loop)
        if self.menu.account_id is not None:
            self.stack.instant_to(self.stack.indexOf(self.menu))
        else:
            self.stack.instant_to(self.stack.indexOf(self.welcome))

    # ---------- Idle Handling ----------
    def eventFilter(self, obj, event):
        if event.type() in (
            QEvent.MouseMove, QEvent.MouseButtonPress,
            QEvent.KeyPress, QEvent.KeyRelease
        ):
            self.idle_timer.start()
        return super().eventFilter(obj, event)

    def _idle_trigger(self):
        dlg = IdleWarningDialog(seconds=10)
        timer = QTimer(self)
        timer.timeout.connect(dlg.tick)
        timer.start(1000)

        if dlg.exec_() == QDialog.Accepted:
            timer.stop()
            self.idle_timer.start()
        else:
            timer.stop()
            self.go_welcome()

    # ---------- Admin Shortcut ----------
    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key_A and
            event.modifiers() & Qt.ControlModifier and
            event.modifiers() & Qt.ShiftModifier
        ):
            if AdminPinDialog().exec_() == QDialog.Accepted:
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

    # ---------- Navigation ----------
    def go_welcome(self):
        # hard reset session state on logout/idle reset
        self.menu.account_id = None
        self.menu.balance = None

        # Reset dynamic screens to prevent stale state
        for scr in (self.transaction, self.history, self.account_info):
            try:
                scr.reset()
            except Exception:
                pass

        # Welcome is safe to animate
        self.stack.fade_to(self.stack.indexOf(self.welcome))

    def go_auth(self):
        # Auth is safe to animate
        self.stack.slide_to(self.stack.indexOf(self.auth))

    def go_admin(self):
        # Admin is mostly static UI; fade is ok
        self.stack.fade_to(self.stack.indexOf(self.admin))

    def go_menu(self, account_id, balance):
        self.menu.set_user(account_id, balance)
        # Menu is safe to animate
        self.stack.slide_to(self.stack.indexOf(self.menu))

    def go_transaction(self, option, account_id, balance):
        # IMPORTANT: Dynamic screens should NOT animate (prevents white screen)

        if option == "info":
            try:
                self.account_info.reset()
            except Exception:
                pass
            self.stack.instant_to(self.stack.indexOf(self.account_info))
            self.account_info.set_account(account_id)
            return

        if option == "statement":
            try:
                self.history.reset()
            except Exception:
                pass
            self.stack.instant_to(self.stack.indexOf(self.history))
            self.history.set_account(account_id)
            return

        # Transfer / bill / deposit
        try:
            self.transaction.reset()
        except Exception:
            pass
        self.stack.instant_to(self.stack.indexOf(self.transaction))
        self.transaction.set_context(option, account_id, balance)

    def go_receipt(self, receipt_data):
        # Receipt should be instant too (repeatable flow)
        self.stack.instant_to(self.stack.indexOf(self.receipt))
        self.receipt.set_receipt(receipt_data)


# ============================================================
#  Boot
# ============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    QTimer.singleShot(100, window.showFullScreen)
    sys.exit(app.exec_())
 