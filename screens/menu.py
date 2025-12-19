# screens/menu.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt


def scale(px: int) -> int:
    """Scale values relative to screen height (800px baseline)."""
    screen_h = QApplication.primaryScreen().size().height()
    return int(px * screen_h / 800)


class MenuScreen(QWidget):
    def __init__(self, next_callback, back_callback):
        super().__init__()

        # Session info
        self.account_id = None
        self.balance = None
        self.next_callback = next_callback

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(scale(18))

        root.addStretch(1)

        # ---------- TITLE ----------
        title = QLabel("Select a Service")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"""
            font-size: {scale(28)}px;
            font-weight: bold;
            color: #0d6efd;
            """
        )
        root.addWidget(title)

        subtitle = QLabel("Choose from available kiosk banking options:")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            f"""
            font-size: {scale(16)}px;
            color: #555;
            """
        )
        root.addWidget(subtitle)

        root.addSpacing(scale(20))

        # ---------- MENU BUTTONS ----------
        self._add_btn(root, "Transfer Funds", "transfer")
        self._add_btn(root, "Pay Bills", "bill")
        self._add_btn(root, "Cash Deposit", "deposit")
        self._add_btn(root, "Account Information", "info")
        self._add_btn(root, "Transaction History", "statement")

        root.addSpacing(scale(25))

        # ---------- LOGOUT ----------
        logout_btn = QPushButton("Logout")
        logout_btn.setMinimumHeight(scale(55))
        logout_btn.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        logout_btn.setStyleSheet(
            f"""
            QPushButton {{
                font-size: {scale(18)}px;
                padding: 12px;
                border-radius: {scale(18)}px;
            }}
            """
        )
        logout_btn.clicked.connect(back_callback)
        root.addWidget(logout_btn)

        root.addStretch(2)

    # -------------------------------------------------
    # Button helper
    # -------------------------------------------------
    def _add_btn(self, layout, label, option):
        btn = QPushButton(label)
        btn.setMinimumHeight(scale(60))
        btn.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        btn.setStyleSheet(
            f"""
            QPushButton {{
                font-size: {scale(20)}px;
                font-weight: 500;
                padding: 14px;
                border-radius: {scale(20)}px;
            }}
            """
        )
        btn.clicked.connect(lambda _, opt=option: self.open_option(opt))
        layout.addWidget(btn)

    # -------------------------------------------------
    # Called after login
    # -------------------------------------------------
    def set_user(self, account_id, balance):
        self.account_id = account_id
        self.balance = balance

    # -------------------------------------------------
    # Route to MainWindow
    # -------------------------------------------------
    def open_option(self, option):
        self.next_callback(option, self.account_id, self.balance)
