# screens/menu.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt


class MenuScreen(QWidget):
    def __init__(self, next_callback, back_callback):
        super().__init__()

        # Session info
        self.account_id = None
        self.balance = None
        self.next_callback = next_callback

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # ---------------- Title ----------------
        title = QLabel("Select a Service")
        title.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #0d6efd; margin-bottom: 10px;"
        )
        layout.addWidget(title, alignment=Qt.AlignCenter)

        sub = QLabel("Choose from available kiosk banking options:")
        sub.setStyleSheet(
            "font-size: 16px; color: #555; margin-bottom: 30px;"
        )
        layout.addWidget(sub, alignment=Qt.AlignCenter)

        # ---------------- Menu Buttons ----------------
        self._add_btn(layout, "Transfer Funds", "transfer")
        self._add_btn(layout, "Pay Bills", "bill")
        self._add_btn(layout, "Cash Deposit", "deposit")
        self._add_btn(layout, "Account Information", "info")
        self._add_btn(layout, "Transaction History", "statement")

        # ---------------- Logout ----------------
        logout_btn = QPushButton("Logout")
        logout_btn.setFixedSize(220, 55)
        logout_btn.setStyleSheet("font-size:18px;")
        logout_btn.clicked.connect(back_callback)
        layout.addWidget(logout_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    # -------------------------------------------------
    # Button helper
    # -------------------------------------------------
    def _add_btn(self, layout, label, option):
        btn = QPushButton(label)
        btn.setFixedSize(300, 60)
        btn.setStyleSheet("font-size: 20px; font-weight: 500;")
        btn.clicked.connect(lambda _, opt=option: self.open_option(opt))
        layout.addWidget(btn, alignment=Qt.AlignCenter)

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
