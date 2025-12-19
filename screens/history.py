# screens/history.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem,
    QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from database.db import get_conn
import sqlite3


class TransactionHistoryScreen(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.account_id = None

        # ---------- Layout ----------
        self.root = QVBoxLayout(self)
        self.root.setAlignment(Qt.AlignCenter)
        self.root.setContentsMargins(30, 25, 30, 25)
        self.root.setSpacing(14)

        self.root.addStretch(1)

        # ---------- Title ----------
        self.title = QLabel("Transaction History")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
            color:#0d6efd;
        """)
        self.root.addWidget(self.title)

        # ---------- Table ----------
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([
            "Transaction Type", "Amount (₱)", "Record ID"
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        self.table.setStyleSheet("""
            QTableWidget {
                font-size:14px;
            }
            QHeaderView::section {
                font-size:15px;
                font-weight:bold;
                padding:6px;
            }
        """)

        self.root.addWidget(self.table, stretch=4)

        # ---------- Back Button ----------
        self.back_btn = QPushButton("Back to Menu")
        self.back_btn.setFixedHeight(56)
        self.back_btn.setMaximumWidth(420)
        self.back_btn.setStyleSheet("""
            QPushButton {
                font-size:18px;
                font-weight:bold;
                padding:12px;
                border-radius:16px;
            }
        """)
        self.back_btn.clicked.connect(self.back_callback)
        self.root.addWidget(self.back_btn, alignment=Qt.AlignCenter)

        self.root.addStretch(1)

        self.reset()

    # ------------------------------------
    # RESET (ABSOLUTELY REQUIRED)
    # ------------------------------------
    def reset(self):
        self.setGraphicsEffect(None)  # 🔥 critical

        self.account_id = None
        self.table.setRowCount(0)
        self.table.clearContents()

        self.update()
        self.repaint()

    # ------------------------------------
    # Load account transactions safely
    # ------------------------------------
    def set_account(self, account_id):
        if account_id is None:
            QMessageBox.warning(self, "Error", "No active session.")
            return

        self.reset()
        self.account_id = account_id

        # Defer DB load until visible
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
                self.table.setItem(r, 1, QTableWidgetItem(f"{float(row[1]):,.2f}"))
                self.table.setItem(r, 2, QTableWidgetItem(str(row[2])))

            self.table.resizeColumnsToContents()
            self.update()
            self.repaint()

        except sqlite3.Error as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to load transaction history:\n{e}"
            )
