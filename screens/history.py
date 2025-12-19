# screens/history.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem,
    QMessageBox, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from database.db import get_conn
import sqlite3


def scale(px: int) -> int:
    screen_h = QApplication.primaryScreen().size().height()
    return int(px * screen_h / 800)


class TransactionHistoryScreen(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.account_id = None

        # ---------- Layout ----------
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(30, 25, 30, 25)
        self.root.setSpacing(scale(14))

        self.root.addStretch(1)

        # ---------- Title ----------
        title = QLabel("Transaction History")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"""
            font-size:{scale(28)}px;
            font-weight:bold;
            color:#0d6efd;
            """
        )
        self.root.addWidget(title)

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

        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                font-size:{scale(14)}px;
            }}
            QHeaderView::section {{
                font-size:{scale(15)}px;
                font-weight:bold;
                padding:6px;
            }}
            """
        )

        self.root.addWidget(self.table, stretch=4)

        # ---------- Back Button ----------
        back_btn = QPushButton("Back to Menu")
        back_btn.setMinimumHeight(scale(55))
        back_btn.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        back_btn.setStyleSheet(
            f"""
            QPushButton {{
                font-size:{scale(18)}px;
                font-weight:bold;
                padding:12px;
                border-radius:{scale(18)}px;
            }}
            """
        )
        back_btn.clicked.connect(self.back_callback)
        self.root.addWidget(back_btn)

        self.root.addStretch(1)

        self.reset()

    # ------------------------------------
    # Reset screen (CRITICAL)
    # ------------------------------------
    def reset(self):
        self.account_id = None
        self.table.setRowCount(0)
        self.table.clearContents()

        self.updateGeometry()
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
            self.updateGeometry()
            self.repaint()

        except sqlite3.Error as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to load transaction history:\n{e}"
            )
