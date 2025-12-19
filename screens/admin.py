# screens/admin.py
import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QLineEdit, QFormLayout
)
from PyQt5.QtCore import Qt

from database.db import get_conn, log_event
from security import hash_pin


class AdminScreen(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # ================= Title =================
        title = QLabel("Admin Panel")
        title.setStyleSheet("font-size:26px;font-weight:bold;")
        root.addWidget(title)

        # ================= Buttons =================
        btn_row = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_all)

        reset_btn = QPushButton("RESET TRANSACTIONS")
        reset_btn.setStyleSheet(
            "background:#dc3545;color:white;font-weight:bold;"
            "padding:8px;border-radius:10px;"
        )
        reset_btn.clicked.connect(self.reset_transactions)

        back_btn = QPushButton("Back to Welcome")
        back_btn.clicked.connect(self.back_callback)

        btn_row.addWidget(refresh_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        btn_row.addWidget(back_btn)
        root.addLayout(btn_row)

        # ================= Accounts Table =================
        root.addWidget(QLabel("Accounts"))

        self.accounts = QTableWidget(0, 3)
        self.accounts.setHorizontalHeaderLabels(
            ["ID", "Card Number", "Balance"]
        )
        self.accounts.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.accounts)

        # ================= Create Account =================
        root.addWidget(QLabel("Create New Account"))

        form = QFormLayout()
        self.in_card = QLineEdit()
        self.in_pin = QLineEdit()
        self.in_pin.setEchoMode(QLineEdit.Password)
        self.in_balance = QLineEdit()

        form.addRow("Card Number:", self.in_card)
        form.addRow("PIN:", self.in_pin)
        form.addRow("Initial Balance:", self.in_balance)

        root.addLayout(form)

        create_btn = QPushButton("Create Account")
        create_btn.setFixedHeight(45)
        create_btn.clicked.connect(self.create_account)
        root.addWidget(create_btn)

        # ================= Audit Log =================
        root.addWidget(QLabel("Audit Log"))

        self.audit = QTableWidget(0, 5)
        self.audit.setHorizontalHeaderLabels(
            ["Time", "Account ID", "Event", "Amount", "Details"]
        )
        self.audit.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.audit)

        self.refresh_all()

    # ====================================================
    # Helpers
    # ====================================================
    def refresh_all(self):
        self.load_accounts()
        self.load_audit()

    def load_accounts(self):
        self.accounts.setRowCount(0)
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("SELECT id, card_number, balance FROM accounts")
            for row in cur.fetchall():
                r = self.accounts.rowCount()
                self.accounts.insertRow(r)
                for c, val in enumerate(row):
                    self.accounts.setItem(r, c, QTableWidgetItem(str(val)))

    def load_audit(self):
        self.audit.setRowCount(0)
        with get_conn() as con:
            cur = con.cursor()
            cur.execute("""
                SELECT ts, account_id, event_type, amount, details
                FROM audit_log
                ORDER BY ts DESC
                LIMIT 200
            """)
            for row in cur.fetchall():
                r = self.audit.rowCount()
                self.audit.insertRow(r)
                for c, val in enumerate(row):
                    self.audit.setItem(r, c, QTableWidgetItem(str(val)))

    # ====================================================
    # Create Account (FIXED – NO DB LOCK)
    # ====================================================
    def create_account(self):
        card = self.in_card.text().strip()
        pin = self.in_pin.text().strip()
        bal_txt = self.in_balance.text().strip()

        if not card or not pin or not bal_txt:
            QMessageBox.warning(self, "Missing fields", "Fill all fields.")
            return

        try:
            balance = float(bal_txt)
            if balance < 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid balance", "Balance must be ≥ 0.")
            return

        try:
            # Hash PIN (PBKDF2)
            pin_blob = hash_pin(pin)
            pin_hash_hex = pin_blob.hex()

            with get_conn() as con:
                cur = con.cursor()

                cur.execute("""
                    INSERT INTO accounts (card_number, pin_hash, balance)
                    VALUES (?, ?, ?)
                """, (card, pin_hash_hex, balance))

                account_id = cur.lastrowid

                # 🔑 IMPORTANT: reuse same connection
                log_event(
                    account_id,
                    "CREATE_ACCOUNT",
                    balance,
                    f"Admin created account {card}",
                    conn=con
                )

                con.commit()

            self.in_card.clear()
            self.in_pin.clear()
            self.in_balance.clear()

            self.refresh_all()
            QMessageBox.information(self, "Success", "Account created.")

        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "Card number already exists.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ====================================================
    # Reset Transactions (FIXED – NO DB LOCK)
    # ====================================================
    def reset_transactions(self):
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "This will DELETE ALL TRANSACTIONS.\nAccounts will remain.\n\nProceed?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            with get_conn() as con:
                cur = con.cursor()
                cur.execute("DELETE FROM transactions")

                # 🔑 IMPORTANT: reuse same connection
                log_event(
                    None,
                    "ADMIN_RESET",
                    details="Transactions wiped",
                    conn=con
                )

                con.commit()

            self.refresh_all()
            QMessageBox.information(self, "Done", "Transactions cleared.")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
