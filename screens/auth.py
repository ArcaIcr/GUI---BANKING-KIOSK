# screens/auth.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QMessageBox, QInputDialog, QLineEdit
)
from PyQt5.QtCore import Qt
import traceback

from database.db import get_conn, log_event
from security import verify_pin


class AuthScreen(QWidget):
    def __init__(self, next_callback, back_callback):
        super().__init__()
        self.next_callback = next_callback

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("User Authentication")
        label.setStyleSheet("font-size: 26px; font-weight: bold; color: #0d6efd;")
        layout.addWidget(label, alignment=Qt.AlignCenter)

        card_btn = QPushButton("Login via Card")
        card_btn.clicked.connect(self.login_card)
        layout.addWidget(card_btn, alignment=Qt.AlignCenter)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(back_callback)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    # -------------------------------------------------
    # Authentication (PBKDF2 – CORRECT)
    # -------------------------------------------------
    def authenticate_user(self, card_number, pin):
        try:
            with get_conn() as con:
                cur = con.cursor()
                cur.execute("""
                    SELECT id, balance, pin_hash
                    FROM accounts
                    WHERE card_number = ?
                """, (card_number,))
                row = cur.fetchone()

                if not row:
                    return None

                account_id, balance, stored_hash_hex = row

                # ✅ Correct verification
                if verify_pin(pin, stored_hash_hex):
                    return account_id, balance

                return None

        except Exception:
            print("\n[ERROR IN authenticate_user]\n")
            traceback.print_exc()
            return None

    # -------------------------------------------------
    # Card login
    # -------------------------------------------------
    def login_card(self):
        try:
            card_number, ok = QInputDialog.getText(
                self, "Card Login", "Enter Card Number:"
            )
            if not ok or not card_number.strip():
                return

            pin, ok = QInputDialog.getText(
                self, "PIN Login", "Enter PIN:", QLineEdit.Password
            )
            if not ok or not pin.strip():
                return

            user = self.authenticate_user(card_number.strip(), pin.strip())

            if user:
                account_id, balance = user
                log_event(account_id, "LOGIN_SUCCESS", details="Card login")
                QMessageBox.information(self, "Success", "Login successful!")
                self.next_callback(account_id, balance)
            else:
                log_event(None, "LOGIN_FAIL", details=f"Card {card_number}")
                QMessageBox.warning(self, "Error", "Invalid card number or PIN.")

        except Exception:
            print("\n[ERROR IN login_card]\n")
            traceback.print_exc()
