# screens/account_info.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from database.db import get_conn


class AccountInfoScreen(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.account_id = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Account Information")
        title.setStyleSheet(
            "font-size:28px;font-weight:bold;color:#0d6efd;"
        )
        layout.addWidget(title)

        self.id_label = QLabel("")
        self.card_label = QLabel("")
        self.balance_label = QLabel("")

        for lbl in (self.id_label, self.card_label, self.balance_label):
            lbl.setStyleSheet("font-size:18px;color:#333;")
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)

        back_btn = QPushButton("Back to Menu")
        back_btn.setFixedSize(220, 55)
        back_btn.clicked.connect(self.back_callback)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)

    # ------------------------------------
    # Reset screen (REQUIRED)
    # ------------------------------------
    def reset(self):
        self.account_id = None
        self.id_label.setText("")
        self.card_label.setText("")
        self.balance_label.setText("")

    # ------------------------------------
    # Load account safely
    # ------------------------------------
    def set_account(self, account_id):
        if account_id is None:
            QMessageBox.warning(self, "Error", "No active session.")
            return

        self.reset()
        self.account_id = account_id

        # Defer DB load until widget is visible
        QTimer.singleShot(0, self._load_data)

    def _load_data(self):
        try:
            with get_conn() as con:
                cur = con.cursor()
                cur.execute(
                    "SELECT id, card_number, balance FROM accounts WHERE id=?",
                    (self.account_id,)
                )
                row = cur.fetchone()

            if not row:
                QMessageBox.warning(self, "Error", "Account not found.")
                return

            acc_id, card, balance = row
            masked = (
                f"**** **** **** {card[-4:]}"
                if card and len(card) >= 4
                else card
            )

            self.id_label.setText(f"Account ID: {acc_id}")
            self.card_label.setText(f"Card Number: {masked}")
            self.balance_label.setText(f"Balance: ₱{balance:,.2f}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to load account info:\n{e}"
            )
