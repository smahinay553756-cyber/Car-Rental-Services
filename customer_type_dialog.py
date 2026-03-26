import pymysql
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QMessageBox, QStackedWidget, QWidget, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from datetime import timedelta
import os

GREEN        = "#22c55e"
GREEN_DARK   = "#16a34a"
GREEN_BG     = "#dcfce7"
GREEN_BORDER = "#bbf7d0"
RED_BG       = "#fee2e2"
RED_DARK     = "#dc2626"
RED_BORDER   = "#fecaca"
BORDER       = "#e2e8f0"
TEXT_PRIMARY = "#0f172a"
TEXT_MUTED   = "#64748b"
SIDEBAR_BG   = "#0f172a"

DB_CFG = {"host": "localhost", "user": "root", "password": "",
          "database": "se_enterprise", "cursorclass": pymysql.cursors.DictCursor, "connect_timeout": 5}

DURATION_DAYS = {"1 Day": 1, "3 Days": 3, "1 Week": 7, "2 Weeks": 14, "3 Weeks": 21}


def _db():
    return pymysql.connect(**DB_CFG)


def _btn(text, color, hover, text_color="#fff", border="none", h=48):
    return (
        f"QPushButton{{background:{color};color:{text_color};border:{border};"
        f"border-radius:10px;font-size:14px;font-weight:700;padding:0 20px;height:{h}px;}}"
        f"QPushButton:hover{{background:{hover};}}"
    )


class CustomerTypeDialog(QDialog):
    """
    Shown right after customer login.
    Emits one of:
      - new_customer()
      - returning_customer(customer_dict, rentals_list)
    """
    new_customer       = pyqtSignal()
    returning_customer = pyqtSignal(dict, list)   # customer row, list of rental rows

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome")
        self.setFixedWidth(440)
        self.setStyleSheet("background:#fff; font-family:'Segoe UI';")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._stack = QStackedWidget(self)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._stack)
        self._stack.addWidget(self._page_choice())   # index 0
        self._stack.addWidget(self._page_id())       # index 1

    # ── Page 0: New or Returning ─────────────────────────────────
    def _page_choice(self):
        w = QWidget(); w.setStyleSheet("background:#fff;")
        lay = QVBoxLayout(w); lay.setContentsMargins(36, 32, 36, 32); lay.setSpacing(0)

        title = QLabel("Welcome!")
        title.setStyleSheet(f"font-size:22px;font-weight:800;color:{TEXT_PRIMARY};background:transparent;")
        lay.addWidget(title)
        lay.addSpacing(6)
        sub = QLabel("Are you a new or returning customer?")
        sub.setStyleSheet(f"font-size:13px;color:{TEXT_MUTED};background:transparent;")
        lay.addWidget(sub)
        lay.addSpacing(28)

        new_btn = QPushButton("New Customer")
        new_btn.setFixedHeight(52)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.setStyleSheet(_btn(GREEN, GREEN, GREEN_DARK))
        new_btn.clicked.connect(self._on_new)
        lay.addWidget(new_btn)
        lay.addSpacing(12)

        ret_btn = QPushButton("Returning Customer")
        ret_btn.setFixedHeight(52)
        ret_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ret_btn.setStyleSheet(
            f"QPushButton{{background:#f8fafc;color:{TEXT_PRIMARY};border:1.5px solid {BORDER};"
            "border-radius:10px;font-size:14px;font-weight:700;padding:0 20px;}}"
            f"QPushButton:hover{{background:#f1f5f9;}}")
        ret_btn.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        lay.addWidget(ret_btn)
        return w

    # ── Page 1: Enter Customer ID ────────────────────────────────
    def _page_id(self):
        w = QWidget(); w.setStyleSheet("background:#fff;")
        lay = QVBoxLayout(w); lay.setContentsMargins(36, 32, 36, 32); lay.setSpacing(0)

        back = QPushButton("← Back")
        back.setFixedHeight(30)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.setStyleSheet(
            f"QPushButton{{background:transparent;color:{TEXT_MUTED};border:none;"
            "font-size:12px;font-weight:600;text-align:left;padding:0;}}"
            f"QPushButton:hover{{color:{TEXT_PRIMARY};}}")
        back.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        lay.addWidget(back)
        lay.addSpacing(12)

        title = QLabel("Enter Your Customer ID")
        title.setStyleSheet(f"font-size:20px;font-weight:800;color:{TEXT_PRIMARY};background:transparent;")
        lay.addWidget(title)
        lay.addSpacing(6)
        sub = QLabel("Enter the ID given to you during your first rental.")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"font-size:12px;color:{TEXT_MUTED};background:transparent;")
        lay.addWidget(sub)
        lay.addSpacing(20)

        fl = QLabel("CUSTOMER ID")
        fl.setStyleSheet(f"font-size:10px;font-weight:700;color:{TEXT_MUTED};letter-spacing:1px;background:transparent;")
        lay.addWidget(fl); lay.addSpacing(6)

        self._id_input = QLineEdit()
        self._id_input.setPlaceholderText("e.g. 1")
        self._id_input.setFixedHeight(48)
        self._id_input.setStyleSheet(
            f"QLineEdit{{background:#f8fafc;border:1.5px solid {BORDER};border-radius:10px;"
            f"padding:12px 16px;font-size:14px;color:{TEXT_PRIMARY};}}"
            f"QLineEdit:focus{{border:1.5px solid {GREEN};}}")
        self._id_input.returnPressed.connect(self._on_proceed)
        lay.addWidget(self._id_input)
        lay.addSpacing(8)

        self._id_error = QLabel("")
        self._id_error.setStyleSheet(f"font-size:11px;color:{RED_DARK};background:transparent;")
        lay.addWidget(self._id_error)
        lay.addSpacing(16)

        proceed = QPushButton("Proceed")
        proceed.setFixedHeight(50)
        proceed.setCursor(Qt.CursorShape.PointingHandCursor)
        proceed.setStyleSheet(_btn(GREEN, GREEN, GREEN_DARK))
        proceed.clicked.connect(self._on_proceed)
        lay.addWidget(proceed)
        return w

    def _on_new(self):
        self.accept()
        self.new_customer.emit()

    def _on_proceed(self):
        raw = self._id_input.text().strip()
        if not raw.isdigit():
            self._id_error.setText("Please enter a valid numeric ID.")
            return
        cid = int(raw)
        try:
            with _db() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM customers WHERE customer_id = %s", (cid,))
                    customer = cur.fetchone()
                    if not customer:
                        self._id_error.setText(f"No customer found with ID {cid}.")
                        return
                    cur.execute("""
                        SELECT r.*, c.car_name, c.car_price
                        FROM rentals r
                        JOIN cars c ON r.car_id = c.car_id
                        WHERE r.customer_id = %s
                        ORDER BY r.rental_id DESC
                    """, (cid,))
                    rentals = cur.fetchall() or []
            self.accept()
            self.returning_customer.emit(dict(customer), [dict(r) for r in rentals])
        except Exception as e:
            self._id_error.setText(f"Error: {e}")
