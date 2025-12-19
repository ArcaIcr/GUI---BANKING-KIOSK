# screens/account_info.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from database.db import get_conn


class AccountInfoScreen(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.account_id = None

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Account Information")
        title.setStyleSheet("font-size:28px;font-weight:bold;color:#0d6efd;")
        layout.addWidget(title)

        self.id_label = QLabel("")
        self.card_label = QLabel("")
        self.balance_label = QLabel("")

        for lbl in (self.id_label, self.card_label, self.balance_label):
            lbl.setStyleSheet("font-size:18px;color:#333;")
            layout.addWidget(lbl, alignment=Qt.AlignCenter)

        back_btn = QPushButton("Back to Menu")
        back_btn.setFixedSize(220, 55)
        back_btn.clicked.connect(self.back_callback)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def set_account(self, account_id):
        self.account_id = account_id

        with get_conn() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id, card_number, balance FROM accounts WHERE id=?",
                (account_id,)
            )
            row = cur.fetchone()

        if not row:
            return

        acc_id, card, balance = row
        masked = f"**** **** **** {card[-4:]}" if len(card) >= 4 else card

        self.id_label.setText(f"Account ID: {acc_id}")
        self.card_label.setText(f"Card Number: {masked}")
        self.balance_label.setText(f"Balance: ₱{balance:,.2f}")
