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
    def __init__(self, next_callback, cancel_callback):
        super().__init__()
        self.next_callback = next_callback
        self.cancel_callback = cancel_callback

        # ---------- Layout ----------
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)

        self.title = QLabel("")
        self.title.setStyleSheet(
            "font-size:26px;font-weight:bold;color:#0d6efd;"
        )
        self.layout.addWidget(self.title, alignment=Qt.AlignCenter)

        self.account_input = QLineEdit()
        self.account_input.setFixedWidth(300)
        self.layout.addWidget(self.account_input, alignment=Qt.AlignCenter)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount (₱)")
        self.amount_input.setFixedWidth(300)
        self.layout.addWidget(self.amount_input, alignment=Qt.AlignCenter)

        # ---------- Action Buttons ----------
        self.confirm_btn = QPushButton("")
        self.confirm_btn.setFixedSize(260, 60)
        self.confirm_btn.clicked.connect(self.process)
        self.layout.addWidget(self.confirm_btn, alignment=Qt.AlignCenter)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedSize(260, 50)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dee2e6;
                color: #333;
                border-radius: 14px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #ced4da;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel)
        self.layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)

        self.setLayout(self.layout)

        # ---------- State ----------
        self.option = None
        self.account_id = None
        self.balance = None

    # -------------------------------------------------
    # RESET (CRITICAL FOR KIOSK REUSE)
    # -------------------------------------------------
    def reset(self):
        self.option = None
        self.account_id = None
        self.balance = None

        self.title.setText("")
        self.account_input.clear()
        self.amount_input.clear()

        self.account_input.show()
        self.confirm_btn.setText("")

    # -------------------------------------------------
    # Context from Menu
    # -------------------------------------------------
    def set_context(self, option, account_id, balance):
        self.reset()

        self.option = option
        self.account_id = account_id
        self.balance = balance

        if option == "transfer":
            self.title.setText("Transfer Funds")
            self.account_input.setPlaceholderText("Recipient Card Number")
            self.account_input.show()
            self.confirm_btn.setText("Confirm Transfer")

        elif option == "bill":
            self.title.setText("Pay Bills")
            self.account_input.setPlaceholderText("Bill Reference / Account No.")
            self.account_input.show()
            self.confirm_btn.setText("Pay Bill")

        elif option == "deposit":
            self.title.setText("Cash Deposit")
            self.account_input.hide()
            self.confirm_btn.setText("Deposit Cash")

        else:
            QMessageBox.warning(self, "Error", "Invalid transaction option.")

    # -------------------------------------------------
    # Cancel → back to menu
    # -------------------------------------------------
    def cancel(self):
        reply = QMessageBox.question(
            self,
            "Cancel Transaction",
            "Are you sure you want to cancel this transaction?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.reset()
            self.cancel_callback()

    # -------------------------------------------------
    # Dispatcher
    # -------------------------------------------------
    def process(self):
        try:
            amount = float(self.amount_input.text().strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid amount.")
            return

        try:
            if self.option == "transfer":
                self._process_transfer(amount)
            elif self.option == "bill":
                self._process_bill(amount)
            elif self.option == "deposit":
                self._process_deposit(amount)
            else:
                QMessageBox.warning(self, "Error", "Unsupported transaction.")
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", "Transaction failed.")

    # -------------------------------------------------
    # Transfer
    # -------------------------------------------------
    def _process_transfer(self, amount):
        recipient = self.account_input.text().strip()
        if not recipient:
            QMessageBox.warning(self, "Error", "Recipient is required.")
            return

        with get_conn() as con:
            cur = con.cursor()

            cur.execute("SELECT balance FROM accounts WHERE id=?", (self.account_id,))
            old_balance = cur.fetchone()[0]

            if amount > old_balance:
                QMessageBox.warning(self, "Error", "Insufficient balance.")
                return

            cur.execute(
                "SELECT id, balance FROM accounts WHERE card_number=?",
                (recipient,)
            )
            rec = cur.fetchone()
            if not rec:
                QMessageBox.warning(self, "Error", "Recipient not found.")
                return

            rec_id, rec_balance = rec
            new_balance = old_balance - amount

            cur.execute(
                "UPDATE accounts SET balance=? WHERE id=?",
                (new_balance, self.account_id)
            )
            cur.execute(
                "UPDATE accounts SET balance=? WHERE id=?",
                (rec_balance + amount, rec_id)
            )
            cur.execute(
                "INSERT INTO transactions(account_id, amount, type) VALUES(?,?,?)",
                (self.account_id, amount, "TRANSFER")
            )
            con.commit()

        log_event(self.account_id, "TRANSFER", amount, f"To {recipient}")
        self._finish("Transfer Funds", amount, old_balance, new_balance, recipient)

    # -------------------------------------------------
    # Bill Payment
    # -------------------------------------------------
    def _process_bill(self, amount):
        bill_ref = self.account_input.text().strip()
        if not bill_ref:
            QMessageBox.warning(self, "Error", "Bill reference required.")
            return

        with get_conn() as con:
            cur = con.cursor()

            cur.execute("SELECT balance FROM accounts WHERE id=?", (self.account_id,))
            old_balance = cur.fetchone()[0]

            if amount > old_balance:
                QMessageBox.warning(self, "Error", "Insufficient balance.")
                return

            new_balance = old_balance - amount

            cur.execute(
                "UPDATE accounts SET balance=? WHERE id=?",
                (new_balance, self.account_id)
            )
            cur.execute(
                "INSERT INTO transactions(account_id, amount, type) VALUES(?,?,?)",
                (self.account_id, amount, "BILL_PAYMENT")
            )
            con.commit()

        log_event(self.account_id, "BILL_PAYMENT", amount, bill_ref)
        self._finish("Bill Payment", amount, old_balance, new_balance, bill_ref)

    # -------------------------------------------------
    # Cash Deposit
    # -------------------------------------------------
    def _process_deposit(self, amount):
        with get_conn() as con:
            cur = con.cursor()

            cur.execute("SELECT balance FROM accounts WHERE id=?", (self.account_id,))
            old_balance = cur.fetchone()[0]

            new_balance = old_balance + amount

            cur.execute(
                "UPDATE accounts SET balance=? WHERE id=?",
                (new_balance, self.account_id)
            )
            cur.execute(
                "INSERT INTO transactions(account_id, amount, type) VALUES(?,?,?)",
                (self.account_id, amount, "CASH_DEPOSIT")
            )
            con.commit()

        log_event(self.account_id, "CASH_DEPOSIT", amount)
        self._finish("Cash Deposit", amount, old_balance, new_balance)

    # -------------------------------------------------
    # Finish → Receipt
    # -------------------------------------------------
    def _finish(self, tx_type, amount, old, new, recipient=None):
        receipt = {
            "type": tx_type,
            "amount": amount,
            "old_balance": old,
            "new_balance": new,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if recipient:
            receipt["recipient"] = recipient

        QMessageBox.information(self, "Success", f"{tx_type} completed.")
        self.next_callback(receipt)
