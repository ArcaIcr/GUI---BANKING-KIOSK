from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

class MenuScreen(QWidget):
    def __init__(self, next_callback, back_callback):
        super().__init__()
        
        # Placeholder for logged-in user
        self.account_id = None
        self.balance = None
        self.next_callback = next_callback

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("Select a Service")
        label.setStyleSheet("font-size: 28px; font-weight: bold; color: #0d6efd; margin-bottom: 10px;")
        layout.addWidget(label, alignment=Qt.AlignCenter)

        sub = QLabel("Choose from available online banking options:")
        sub.setStyleSheet("font-size: 16px; color: #555; margin-bottom: 30px;")
        layout.addWidget(sub, alignment=Qt.AlignCenter)

        # Menu buttons
        options = ["Transfer Funds", "Pay Bills", "Account Information", "Request e-Statement"]
        for option in options:
            btn = QPushButton(option)
            btn.setFixedSize(300, 60)
            btn.setStyleSheet("font-size: 20px; font-weight: 500;")
            btn.clicked.connect(lambda _, opt=option: self.open_option(opt))
            layout.addWidget(btn, alignment=Qt.AlignCenter)

        back_btn = QPushButton("Logout")
        back_btn.setFixedSize(200, 50)
        back_btn.clicked.connect(back_callback)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    # Called by AuthScreen to set the user's logged-in info
    def set_user(self, account_id, balance):
        self.account_id = account_id
        self.balance = balance

    def open_option(self, selected_option):
        # Pass the option + user info forward
        self.next_callback(selected_option, self.account_id, self.balance)
