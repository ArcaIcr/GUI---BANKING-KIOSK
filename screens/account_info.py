# screens/account_info.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QMessageBox, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from database.db import get_conn


def scale(px: int) -> int:
    screen_h = QApplication.primaryScreen().size().height()
    return int(px * screen_h / 800)


class AccountInfoScreen(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.account_id = None

        # ---------- Layout ----------
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(40, 30, 40, 30)
        self.root.setSpacing(scale(16))

        self.root.addStretch(1)

        # ---------- Title ----------
        self.title = QLabel("Account Information")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet(
            f"""
            font-size:{scale(28)}px;
            font-weight:bold;
            color:#0d6efd;
            """
        )
        self.root.addWidget(self.title)

        # ---------- Info Labels ----------
        self.id_label = QLabel("")
        self.card_label = QLabel("")
        self.balance_label = QLabel("")

        for lbl in (self.id_label, self.card_label, self.balance_label):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"font-size:{scale(18)}px;color:#333;"
            )
            lbl.setWordWrap(True)
            self.root.addWidget(lbl)

        self.root.addSpacing(scale(25))

        # ---------- Back Button ----------
        self.back_btn = QPushButton("Back to Menu")
        self.back_btn.setMinimumHeight(scale(55))
        self.back_btn.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        self.back_btn.setStyleSheet(
            f"""
            QPushButton {{
                font-size:{scale(18)}px;
                font-weight:bold;
                padding:12px;
                border-radius:{scale(18)}px;
            }}
            """
        )
        self.back_btn.clicked.connect(self.back_callback)
        self.root.addWidget(self.back_btn)

        self.root.addStretch(2)

        self.reset()

    # ------------------------------------
    # Reset screen (CRITICAL)
    # ------------------------------------
    def reset(self):
        self.account_id = None
        self.id_label.setText("")
        self.card_label.setText("")
        self.balance_label.setText("")

        self.updateGeometry()
        self.repaint()

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

            # Force repaint (prevents blank screen)
            self.updateGeometry()
            self.repaint()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to load account info:\n{e}"
            )
