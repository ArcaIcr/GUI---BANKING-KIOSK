# screens/transaction.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from datetime import datetime
import traceback

from database.db import get_conn, log_event


class TransactionScreen(QWidget):
    def __init__(self, next_callback):
        super().__init__()
        self.next_callback = next_callback

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("Transfer / Payment Details")
        label.setStyleSheet("font-size:26px;font-weight:bold;color:#0d6efd;")
        layout.addWidget(label, alignment=Qt.AlignCenter)

        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("Recipient Card Number")
        self.account_input.setFixedWidth(300)
        layout.addWidget(self.account_input, alignment=Qt.AlignCenter)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount (₱)")
        self.amount_input.setFixedWidth(300)
        layout.addWidget(self.amount_input, alignment=Qt.AlignCenter)

        confirm_btn = QPushButton("Confirm Transaction")
        confirm_btn.setFixedSize(260, 60)
        confirm_btn.clicked.connect(self.process)
        layout.addWidget(confirm_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

        # context
        self.option = None
        self.account_id = None
        self.balance = None

    def set_context(self, option, account_id, balance):
        self.option = option
        self.account_id = account_id
        self.balance = balance

    # -------------------------------------------------
    # Process Transfer
    # -------------------------------------------------
    def process(self):
        acc = self.account_input.text().strip()
        amt_str = self.amount_input.text().strip()

        if not acc or not amt_str:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return

        # Validate amount
        try:
            amount = float(amt_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid amount.")
            return

        try:
            with get_conn() as con:
                cur = con.cursor()

                # Get sender balance
                cur.execute(
                    "SELECT balance FROM accounts WHERE id = ?",
                    (self.account_id,)
                )
                row = cur.fetchone()
                if not row:
                    QMessageBox.warning(self, "Error", "Account not found.")
                    return

                old_balance = row[0]

                if amount > old_balance:
                    log_event(
                        self.account_id,
                        "TRANSFER_FAIL",
                        amount,
                        "Insufficient balance"
                    )
                    QMessageBox.warning(self, "Error", "Insufficient balance.")
                    return

                # Get recipient
                cur.execute(
                    "SELECT id, balance FROM accounts WHERE card_number = ?",
                    (acc,)
                )
                rec = cur.fetchone()
                if not rec:
                    log_event(
                        self.account_id,
                        "TRANSFER_FAIL",
                        amount,
                        "Recipient not found"
                    )
                    QMessageBox.warning(self, "Error", "Recipient account does not exist.")
                    return

                rec_id, rec_balance = rec

                # Perform atomic transfer
                new_balance = old_balance - amount
                new_rec_balance = rec_balance + amount

                cur.execute(
                    "UPDATE accounts SET balance = ? WHERE id = ?",
                    (new_balance, self.account_id)
                )
                cur.execute(
                    "UPDATE accounts SET balance = ? WHERE id = ?",
                    (new_rec_balance, rec_id)
                )

                # Transaction record
                cur.execute("""
                    INSERT INTO transactions (account_id, amount, type)
                    VALUES (?, ?, ?)
                """, (self.account_id, amount, "TRANSFER"))

                con.commit()

            # Audit logs (after commit)
            log_event(
                self.account_id,
                "TRANSFER",
                amount,
                f"To card {acc} | Balance {old_balance} → {new_balance}"
            )
            log_event(
                rec_id,
                "TRANSFER_IN",
                amount,
                f"From account {self.account_id}"
            )

            # Prepare receipt
            receipt = {
                "type": "Transfer Funds",
                "recipient": acc,
                "amount": amount,
                "old_balance": old_balance,
                "new_balance": new_balance,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            QMessageBox.information(self, "Success", "Transfer completed.")
            self.next_callback(receipt)

        except Exception:
            print("\n[ERROR IN TransactionScreen.process]\n")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", "Transaction failed unexpectedly.")
