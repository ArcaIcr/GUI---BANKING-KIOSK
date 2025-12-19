import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QSpacerItem, QSizePolicy, QApplication
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


# -------------------------------
# Responsive helpers (KIOSK SAFE)
# -------------------------------
def scale_h(px):
    return int(px * QApplication.primaryScreen().size().height() / 800)


def scale_w(px):
    return int(px * QApplication.primaryScreen().size().width() / 1280)


class WelcomeScreen(QWidget):
    def __init__(self, next_callback):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Top spacer
        layout.addSpacerItem(
            QSpacerItem(20, scale_h(80), QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # ---------------- Logo ----------------
        logo = QLabel()
        base_dir = os.path.dirname(__file__)
        logo_path = os.path.join(base_dir, "..", "styles", "logo.png")

        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    scale_h(160),
                    scale_h(160),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )

        layout.addWidget(logo, alignment=Qt.AlignCenter)

        # ---------------- Title ----------------
        label = QLabel("Welcome to Nyxon Online Banking Kiosk")
        label.setStyleSheet(f"""
            font-size: {scale_h(28)}px;
            font-weight: bold;
            color: #0d6efd;
        """)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # ---------------- Subtitle ----------------
        sub = QLabel("Access your account securely and conveniently.")
        sub.setStyleSheet(f"""
            font-size: {scale_h(18)}px;
            color: #555;
            margin-bottom: {scale_h(24)}px;
        """)
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)

        # ---------------- CTA BUTTON (FIXED) ----------------
        start_btn = QPushButton("Tap to Continue")

        start_btn.setMinimumHeight(scale_h(56))
        start_btn.setMaximumWidth(scale_w(520))   # 🔑 prevents stupid-wide button
        start_btn.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed
        )

        start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0d6efd;
                color: white;
                border-radius: {scale_h(18)}px;
                font-size: {scale_h(20)}px;
                font-weight: bold;
                padding: {scale_h(12)}px {scale_w(24)}px;
            }}
            QPushButton:hover {{
                background-color: #0b5ed7;
            }}
        """)

        start_btn.clicked.connect(next_callback)
        layout.addWidget(start_btn, alignment=Qt.AlignCenter)

        # Bottom spacer
        layout.addSpacerItem(
            QSpacerItem(20, scale_h(80), QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
