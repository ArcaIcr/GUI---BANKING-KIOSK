import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class WelcomeScreen(QWidget):
    def __init__(self, next_callback):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        layout.addSpacerItem(
            QSpacerItem(20, 60, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        logo = QLabel()
        base_dir = os.path.dirname(__file__)
        logo_path = os.path.join(base_dir, "..", "styles", "logo.png")

        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    200, 200,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )

        layout.addWidget(logo, alignment=Qt.AlignCenter)

        label = QLabel("Welcome to Nyxon Online Banking Kiosk")
        label.setStyleSheet(
            "font-size:30px;font-weight:bold;color:#0d6efd;"
        )
        layout.addWidget(label, alignment=Qt.AlignCenter)

        sub = QLabel("Access your account securely and conveniently.")
        sub.setStyleSheet("font-size:18px;color:#555;margin-bottom:30px;")
        layout.addWidget(sub, alignment=Qt.AlignCenter)

        start_btn = QPushButton("Tap to Continue")
        start_btn.setFixedSize(260, 70)
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border-radius: 20px;
                font-size: 22px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
        """)
        start_btn.clicked.connect(next_callback)

        layout.addWidget(start_btn, alignment=Qt.AlignCenter)

        layout.addSpacerItem(
            QSpacerItem(20, 60, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
