# screens/receipt.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QSizePolicy
)
from PyQt5.QtCore import Qt


class ReceiptScreen(QWidget):
    def __init__(self, next_callback):
        super().__init__()
        self.next_callback = next_callback

        # ---------- Layout ----------
        self.root = QVBoxLayout(self)
        self.root.setAlignment(Qt.AlignCenter)
        self.root.setContentsMargins(40, 30, 40, 30)
        self.root.setSpacing(16)

        self.root.addStretch(1)

        # ---------- Title ----------
        self.title = QLabel("Transaction Complete 🧾")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
            color:#0d6efd;
        """)
        self.root.addWidget(self.title)

        # ---------- Dynamic Labels ----------
        self.type_label = QLabel("")
        self.type_label.setAlignment(Qt.AlignCenter)
        self.type_label.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#333;"
        )
        self.root.addWidget(self.type_label)

        self.amount_label = QLabel("")
        self.amount_label.setAlignment(Qt.AlignCenter)
        self.amount_label.setStyleSheet(
            "font-size:18px;color:#555;"
        )
        self.root.addWidget(self.amount_label)

        self.recipient_label = QLabel("")
        self.recipient_label.setAlignment(Qt.AlignCenter)
        self.recipient_label.setStyleSheet(
            "font-size:18px;color:#555;"
        )
        self.root.addWidget(self.recipient_label)

        self.balance_label = QLabel("")
        self.balance_label.setAlignment(Qt.AlignCenter)
        self.balance_label.setStyleSheet(
            "font-size:18px;color:#555;"
        )
        self.root.addWidget(self.balance_label)

        self.time_label = QLabel("")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet(
            "font-size:16px;color:#777;"
        )
        self.root.addWidget(self.time_label)

        self.root.addSpacing(24)

        # ---------- Done Button (CLAMPED WIDTH) ----------
        self.done_btn = QPushButton("Return to Home")
        self.done_btn.setFixedHeight(56)
        self.done_btn.setMaximumWidth(420)   # 🔒 prevents exaggerated width
        self.done_btn.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        self.done_btn.setStyleSheet("""
            QPushButton {
                font-size:20px;
                font-weight:bold;
                padding:12px;
                border-radius:16px;
            }
        """)
        self.done_btn.clicked.connect(self.next_callback)
        self.root.addWidget(self.done_btn, alignment=Qt.AlignCenter)

        self.root.addStretch(2)

        self.reset()

    # -------------------------------------------------
    # RESET (ABSOLUTELY REQUIRED)
    # -------------------------------------------------
    def reset(self):
        self.setGraphicsEffect(None)  # 🔥 CRITICAL

        self.type_label.setText("")
        self.amount_label.setText("")
        self.recipient_label.setText("")
        self.balance_label.setText("")
        self.time_label.setText("")
        self.recipient_label.hide()

        self.update()
        self.repaint()

    # -------------------------------------------------
    # RECEIVE DATA FROM Transaction
    # -------------------------------------------------
    def set_receipt(self, data):
        self.reset()

        self.type_label.setText(f"Transaction Type: {data['type']}")
        self.amount_label.setText(f"Amount: ₱{data['amount']:.2f}")

        recipient = data.get("recipient")
        if recipient:
            self.recipient_label.setText(f"Recipient: {recipient}")
            self.recipient_label.show()
        else:
            self.recipient_label.hide()

        self.balance_label.setText(
            f"Balance: ₱{data['old_balance']:.2f} → ₱{data['new_balance']:.2f}"
        )

        self.time_label.setText(f"Timestamp: {data['timestamp']}")
