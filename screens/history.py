# screens/history.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from database.db import get_conn
import sqlite3


class TransactionHistoryScreen(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.account_id = None

        layout = QVBoxLayout(self)

        title = QLabel("Transaction History")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:28px;font-weight:bold;color:#0d6efd;")
        layout.addWidget(title)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([
            "Transaction Type", "Amount", "Record ID"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        back_btn = QPushButton("Back to Menu")
        back_btn.setFixedSize(220, 55)
        back_btn.clicked.connect(self.back_callback)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)

    # ------------------------------------
    # Reset screen (REQUIRED)
    # ------------------------------------
    def reset(self):
        self.account_id = None
        self.table.setRowCount(0)

    # ------------------------------------
    # Load account transactions safely
    # ------------------------------------
    def set_account(self, account_id):
        if account_id is None:
            QMessageBox.warning(self, "Error", "No active session.")
            return

        self.reset()
        self.account_id = account_id
        QTimer.singleShot(0, self.load_data)

    def load_data(self):
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
                self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
                self.table.setItem(r, 1, QTableWidgetItem(f"{float(row[1]):.2f}"))
                self.table.setItem(r, 2, QTableWidgetItem(str(row[2])))

        except sqlite3.Error as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to load transaction history:\n{e}"
            )
