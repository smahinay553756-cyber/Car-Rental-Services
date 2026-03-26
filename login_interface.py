import os, shutil
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGraphicsDropShadowEffect, QFrame)
from PyQt6.QtGui import QPixmap, QColor, QImage, QPainter, QPainterPath
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QSize
from controller.auth_controller import AuthController

GREEN        = "#22c55e"
GREEN_DARK   = "#16a34a"
SIDEBAR_BG   = "#0f172a"
BORDER       = "#e2e8f0"
TEXT_PRIMARY = "#0f172a"
TEXT_MUTED   = "#64748b"

STYLE = f"""
* {{ font-family: 'Segoe UI', sans-serif; }}
QWidget#loginPage {{ background: {SIDEBAR_BG}; }}
QLabel#headline {{ font-size: 32px; font-weight: 800; color: #000000; letter-spacing: -1px; }}
QLabel#subline  {{ font-size: 14px; color: {TEXT_MUTED}; }}
QLabel#fLabel   {{ font-size: 11px; font-weight: 700; color: {TEXT_MUTED}; letter-spacing: 1px; }}
QLineEdit#inp {{
    background: #f8fafc; border: 1.5px solid {BORDER};
    border-radius: 10px; padding: 14px 16px;
    font-size: 14px; color: {TEXT_PRIMARY};
}}
QLineEdit#inp:focus {{ border: 1.5px solid {GREEN}; background: #fff; }}
QPushButton#loginBtn {{
    background: {GREEN}; color: #fff; border: none;
    border-radius: 10px; font-size: 15px; font-weight: 700; padding: 15px;
}}
QPushButton#loginBtn:hover   {{ background: {GREEN_DARK}; }}
QPushButton#loginBtn:pressed {{ background: #15803d; }}
"""


class RoundedLogoLabel(QLabel):
    """Renders SE.jpg cropped to a circle — works on both dark and light backgrounds."""
    def __init__(self, img_path, size=44, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self._pm = None
        if os.path.exists(img_path):
            src = QPixmap(img_path).scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            # Crop to square from centre
            if src.width() != size or src.height() != size:
                x = (src.width()-size)//2; y = (src.height()-size)//2
                src = src.copy(x, y, size, size)
            self._pm = src

    def paintEvent(self, ev):
        if not self._pm:
            super().paintEvent(ev); return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, self._size, self._size)
        p.setClipPath(path)
        p.drawPixmap(0, 0, self._pm)
        p.end()


class LoginInterface(QWidget):
    login_successful = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setObjectName("loginPage")
        self.setStyleSheet(STYLE)
        self.auth_controller = AuthController()
        self._logo_path = os.path.join(os.getcwd(), "resources", "SE.jpg")
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(self._left_panel(), stretch=45)
        root.addWidget(self._right_panel(), stretch=55)

    # ── LEFT dark panel ──────────────────────────────────────────
    def _left_panel(self):
        w = QWidget(); w.setStyleSheet(f"background:{SIDEBAR_BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(52, 48, 52, 44); lay.setSpacing(0)

        # Brand row with REAL logo
        lr = QHBoxLayout()
        logo = RoundedLogoLabel(self._logo_path, 44)
        lr.addWidget(logo); lr.addSpacing(12)

        brand_col = QVBoxLayout(); brand_col.setSpacing(1)
        b1 = QLabel("SE Enterprise")
        b1.setStyleSheet("font-size:14px;font-weight:700;color:#f1f5f9;"
                         "background:transparent;letter-spacing:0.2px;")
        b2 = QLabel("Fleet Management System")
        b2.setStyleSheet("font-size:10px;color:rgba(255,255,255,0.38);background:transparent;")
        brand_col.addWidget(b1); brand_col.addWidget(b2)
        lr.addLayout(brand_col); lr.addStretch()

        dot_row = QHBoxLayout(); dot_row.setSpacing(5)
        dot = QLabel("●")
        dot.setStyleSheet(f"font-size:7px;color:{GREEN};background:transparent;")
        live = QLabel("Live")
        live.setStyleSheet(f"font-size:11px;color:{GREEN};font-weight:600;background:transparent;")
        dot_row.addWidget(dot); dot_row.addWidget(live)
        lr.addLayout(dot_row)
        lay.addLayout(lr)

        lay.addStretch()

        hero = QLabel("Drive Your\nBusiness\nForward.")
        hero.setStyleSheet("font-size:32px;font-weight:800;color:#fff;"
                           "background:transparent;line-height:1.2;")
        lay.addWidget(hero); lay.addSpacing(16)

        sub = QLabel("A complete car rental management\nplatform for staff and customers.")
        sub.setStyleSheet("font-size:14px;color:rgba(255,255,255,0.52);"
                          "background:transparent;")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        lay.addStretch()

        # Chips
        sr = QHBoxLayout(); sr.setSpacing(10)
        for lbl, val in [("Fleet", "Active"), ("System", "Online")]:
            sr.addWidget(self._stat_chip(lbl, val))
        sr.addStretch()
        lay.addLayout(sr)
        return w

    def _stat_chip(self, label, val):
        c = QFrame(); c.setFixedHeight(58)
        c.setStyleSheet("QFrame{background:rgba(255,255,255,0.06);border-radius:12px;"
                        "border:1px solid rgba(255,255,255,0.09);}")
        ly = QVBoxLayout(c); ly.setContentsMargins(16,10,16,10); ly.setSpacing(2)
        v = QLabel(val)
        v.setStyleSheet(f"font-size:14px;font-weight:700;color:{GREEN};"
                        "background:transparent;border:none;")
        l = QLabel(label)
        l.setStyleSheet("font-size:10px;color:rgba(255,255,255,0.38);"
                        "background:transparent;border:none;")
        ly.addWidget(v); ly.addWidget(l)
        return c

    # ── RIGHT white form panel ───────────────────────────────────
    def _right_panel(self):
        w = QWidget(); w.setStyleSheet("background:#fff;")
        outer = QVBoxLayout(w); outer.setContentsMargins(0,0,0,0)
        outer.addStretch()

        mid = QHBoxLayout(); mid.addStretch()
        card = QWidget(); card.setFixedWidth(420)
        lay = QVBoxLayout(card); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        greet = QLabel("Welcome back"); greet.setObjectName("subline")
        lay.addWidget(greet); lay.addSpacing(8)

        head = QLabel("Sign in to\nyour account"); head.setObjectName("headline")
        lay.addWidget(head); lay.addSpacing(32)

        # Username
        fl = QLabel("USERNAME"); fl.setObjectName("fLabel")
        lay.addWidget(fl); lay.addSpacing(6)
        self.username_input = QLineEdit(); self.username_input.setObjectName("inp")
        self.username_input.setPlaceholderText("Enter your username"); self.username_input.setFixedHeight(52)
        lay.addWidget(self.username_input); lay.addSpacing(16)

        # Password
        fl2 = QLabel("PASSWORD"); fl2.setObjectName("fLabel")
        lay.addWidget(fl2); lay.addSpacing(6)

        pw_wrap = QWidget(); pw_wrap.setFixedHeight(52)
        pw_wrap.setStyleSheet("background:transparent;")
        pw_row = QHBoxLayout(pw_wrap); pw_row.setContentsMargins(0,0,0,0); pw_row.setSpacing(0)

        self.password_input = QLineEdit(); self.password_input.setObjectName("inp")
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.login)
        self.password_input.textChanged.connect(self._check_password_live)

        self._eye_btn = QPushButton("show")
        self._eye_btn.setFixedSize(44, 52)
        self._eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._eye_btn.setCheckable(True)
        self._eye_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;font-size:16px;color:#94a3b8;}"
            "QPushButton:hover{color:#0f172a;}"
            "QPushButton:checked{color:#22c55e;}")
        self._eye_btn.toggled.connect(self._toggle_password_visibility)

        pw_row.addWidget(self.password_input, stretch=1)
        pw_row.addWidget(self._eye_btn)
        lay.addWidget(pw_wrap); lay.addSpacing(6)

        self._pw_status = QLabel("")
        self._pw_status.setFixedHeight(18)
        self._pw_status.setStyleSheet("font-size:11px;background:transparent;")
        lay.addWidget(self._pw_status); lay.addSpacing(10)

        lay.addSpacing(6)
        btn = QPushButton("Login")
        btn.setFixedHeight(54); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.login)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {GREEN}; color: #fff; border: none;
                border-radius: 10px; font-size: 15px; font-weight: 700; padding: 15px;
            }}
            QPushButton:hover   {{ background: {GREEN_DARK}; }}
            QPushButton:pressed {{ background: #15803d; }}
        """)
        lay.addWidget(btn); lay.addSpacing(22)

        note_row = QHBoxLayout()
        note = QLabel("Secure login · SE Enterprise v2.0")
        note.setStyleSheet("font-size:11px;color:#94a3b8;background:transparent;")
        note_row.addStretch(); note_row.addWidget(note); note_row.addStretch()
        lay.addLayout(note_row)

        mid.addWidget(card); mid.addStretch()
        outer.addLayout(mid); outer.addStretch()

        foot = QLabel("© 2025 SE Enterprise. All rights reserved.")
        foot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        foot.setStyleSheet("font-size:11px;color:#cbd5e1;padding:16px;background:transparent;")
        outer.addWidget(foot)
        return w

    def _toggle_password_visibility(self, checked):
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._eye_btn.setText("hide")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._eye_btn.setText("show")

    def _check_password_live(self, text):
        if not text:
            self._pw_status.setText("")
            return
        username = self.username_input.text().strip()
        if not username:
            self._pw_status.setText("")
            return
        user_type, _ = self.auth_controller.login(username, text)
        if user_type:
            self._pw_status.setText("Password correct")
            self._pw_status.setStyleSheet("font-size:11px;background:transparent;color:#16a34a;font-weight:600;")
        else:
            self._pw_status.setText("Incorrect password")
            self._pw_status.setStyleSheet("font-size:11px;background:transparent;color:#dc2626;font-weight:600;")

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        user_type, error = self.auth_controller.login(username, password)
        if user_type:
            self.login_successful.emit(user_type, username)
        else:
            QMessageBox.warning(self, "Login Failed", error)