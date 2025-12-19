# screens/history.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt
from database.db import get_conn
import sqlite3


class TransactionHistoryScreen(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.account_id = None

        layout = QVBoxLayout()

        title = QLabel("Transaction History")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:28px;font-weight:bold;color:#0d6efd;")
        layout.addWidget(title)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([
            "Transaction Type", "Amount", "Record ID"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        back_btn = QPushButton("Back to Menu")
        back_btn.setFixedSize(220, 55)
        back_btn.clicked.connect(self.back_callback)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    # ------------------------------------
    # Load account transactions safely
    # ------------------------------------
    def set_account(self, account_id):
        if account_id is None:
            QMessageBox.warning(self, "Error", "No active session.")
            return

        self.account_id = account_id
        self.load_data()

    def load_data(self):
        self.table.setRowCount(0)

        try:
            with get_conn() as con:
                cur = con.cursor()
                cur.execute("""
                    SELECT type, amount, id
                    FROM transactions
                    WHERE account_id = ?
                    ORDER BY id DESC
                    LIMIT 20
                """, (self.account_id,))
                rows = cur.fetchall()

            for row in rows:
                r = self.table.rowCount()
                self.table.insertRow(r)
                for c, val in enumerate(row):
                    self.table.setItem(r, c, QTableWidgetItem(str(val)))

        except sqlite3.Error as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to load transaction history:\n{e}"
            )
