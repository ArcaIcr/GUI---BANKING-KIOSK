from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt


class ReceiptScreen(QWidget):
    def __init__(self, next_callback):
        super().__init__()
        self.next_callback = next_callback

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Transaction Complete 🧾")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0d6efd; margin-bottom: 10px;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # Dynamic receipt labels
        self.type_label = QLabel("")
        self.type_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        layout.addWidget(self.type_label, alignment=Qt.AlignCenter)

        self.amount_label = QLabel("")
        self.amount_label.setStyleSheet("font-size: 18px; color: #555;")
        layout.addWidget(self.amount_label, alignment=Qt.AlignCenter)

        self.recipient_label = QLabel("")
        self.recipient_label.setStyleSheet("font-size: 18px; color: #555;")
        layout.addWidget(self.recipient_label, alignment=Qt.AlignCenter)

        self.balance_label = QLabel("")
        self.balance_label.setStyleSheet("font-size: 18px; color: #555;")
        layout.addWidget(self.balance_label, alignment=Qt.AlignCenter)

        self.time_label = QLabel("")
        self.time_label.setStyleSheet("font-size: 16px; color: #777; margin-top: 10px;")
        layout.addWidget(self.time_label, alignment=Qt.AlignCenter)

        done_btn = QPushButton("Return to Home")
        done_btn.setFixedSize(240, 60)
        done_btn.clicked.connect(self.next_callback)
        layout.addWidget(done_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    # ------------------------------
    # RECEIVE DATA FROM Transaction
    # ------------------------------
    def set_receipt(self, data):
        """
        data = {
            "type": "Transfer Funds",
            "recipient": "123456",
            "amount": 500,
            "old_balance": 1500,
            "new_balance": 1000,
            "timestamp": "2025-11-29 18:30:22"
        }
        """

        self.type_label.setText(f"Transaction Type: {data['type']}")
        self.amount_label.setText(f"Amount: ₱{data['amount']:.2f}")
        self.recipient_label.setText(f"Recipient: {data['recipient']}")
        self.balance_label.setText(
            f"Balance: ₱{data['old_balance']:.2f} → ₱{data['new_balance']:.2f}"
        )
        self.time_label.setText(f"Timestamp: {data['timestamp']}")
