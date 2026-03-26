from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QComboBox, QScrollArea, QFrame, QGridLayout,
    QDialog, QGraphicsDropShadowEffect, QSizePolicy, QSpacerItem, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QDate
from PyQt6.QtGui import QPixmap, QColor, QImage, QPainter
from datetime import date
from controller.pdf_service import PdfService
import os

GREEN        = "#22c55e"
GREEN_DARK   = "#16a34a"
GREEN_BG     = "#dcfce7"
GREEN_BORDER = "#bbf7d0"
RED          = "#ef4444"
RED_DARK     = "#dc2626"
RED_BG       = "#fee2e2"
RED_BORDER   = "#fecaca"
SIDEBAR_BG   = "#0f172a"
CONTENT_BG   = "#f8fafc"
CARD_BG      = "#ffffff"
BORDER       = "#e2e8f0"
TEXT_PRIMARY = "#0f172a"
TEXT_MUTED   = "#64748b"

STYLE = f"""
* {{ font-family: 'Segoe UI', 'SF Pro Display', sans-serif; }}
QWidget#customerPage {{ background: {CONTENT_BG}; }}

QWidget#topBar {{
    background: {SIDEBAR_BG};
    border-bottom: 1px solid rgba(255,255,255,0.08);
}}
QLabel#appTitle {{
    font-size: 17px; font-weight: 700; color: #f1f5f9; letter-spacing: -0.2px;
}}
QLabel#secHeader {{
    font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 1.2px;
}}

/* Car cards */
QFrame#carCard {{
    background: #ffffff;
    border-radius: 14px;
    border: 1.5px solid {BORDER};
}}
QFrame#carCard:hover {{ border: 1.5px solid {GREEN}; background: #f0fdf4; }}
QFrame#carCard[selected="true"] {{
    border: 2px solid {GREEN};
    background: #f0fdf4;
}}

/* Form panel */
QFrame#formPanel {{
    background: #ffffff;
    border-radius: 16px;
    border: 1px solid {BORDER};
}}
QLabel#formTitle {{ font-size: 16px; font-weight: 800; color: {TEXT_PRIMARY}; }}
QLabel#fLabel    {{ font-size: 10px; font-weight: 700; color: {TEXT_MUTED}; letter-spacing: 1px; }}

QFrame#formPanel, QFrame#formPanel * {{
    background: #ffffff;
}}
QFrame#formPanel QLabel#fLabel {{ color: {TEXT_MUTED}; font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
QFrame#formPanel QLabel#formTitle {{ color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 800; }}
QFrame#formPanel QLineEdit#inp {{
    background: #f8fafc; border: 1.5px solid {BORDER}; border-radius: 9px;
    padding: 11px 14px; font-size: 13px; color: {TEXT_PRIMARY};
}}
QFrame#formPanel QLineEdit#inp:focus {{ border: 1.5px solid {GREEN}; background: #ffffff; }}
QFrame#formPanel QLineEdit#inp[readOnly="true"] {{ background: #f1f5f9; color: {TEXT_MUTED}; font-weight: 700; font-size: 14px; }}
QFrame#formPanel QComboBox#combo {{
    background: #f8fafc; border: 1.5px solid {BORDER}; border-radius: 9px;
    padding: 11px 14px; font-size: 13px; color: {TEXT_PRIMARY};
}}
QFrame#formPanel QComboBox#combo::drop-down {{ border: none; width: 28px; }}
QFrame#formPanel QComboBox#combo QAbstractItemView {{
    background: #ffffff; border: 1px solid {BORDER}; selection-background-color: {GREEN_BG};
}}
QFrame#formPanel QFrame {{ background: #f8fafc; border-radius: 10px; }}

QPushButton#rentBtn {{
    background: {GREEN};
    color: #fff; border: none;
    border-radius: 10px;
    font-size: 15px; font-weight: 700; padding: 14px;
}}
QPushButton#rentBtn:hover   {{ background: {GREEN_DARK}; }}
QPushButton#rentBtn:pressed {{ background: #15803d; }}

QPushButton#logoutBtn {{
    background: transparent;
    color: {TEXT_MUTED};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    font-size: 12px; font-weight: 600;
    padding: 7px 14px;
}}
QPushButton#logoutBtn:hover {{ background: {TEXT_PRIMARY}; color: #fff; border-color: {TEXT_PRIMARY}; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 5px; border-radius: 3px; }}
QScrollBar::handle:vertical {{ background: #cbd5e1; border-radius: 3px; min-height: 20px; }}
QScrollBar::handle:vertical:hover {{ background: #94a3b8; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
"""


class CustomerInterface(QWidget):
    logout_requested = pyqtSignal()
    rental_confirmed = pyqtSignal(dict)  # emits rental info dict

    def __init__(self):
        super().__init__()
        self.setObjectName("customerPage")
        self.setStyleSheet(STYLE)
        self.cars_data = []
        self.rented_car_ids = set()
        self._car_cards = {}
        self.selected_car = None
        self.pdf_service = PdfService()
        self.logo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "resources", "SE.jpg")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._top_bar())

        body = QWidget(); body.setStyleSheet("background:#0f172a;")
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(24, 20, 24, 20)
        body_lay.setSpacing(20)

        # ── Left: vehicle grid ───────────────────────────────────
        left = QWidget(); left.setStyleSheet("background:transparent;")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0); left_lay.setSpacing(10)

        sec_row = QHBoxLayout()
        sec = QLabel("AVAILABLE VEHICLES"); sec.setObjectName("secHeader")
        sec_row.addWidget(sec); sec_row.addStretch()
        self._vehicle_count = QLabel("")
        self._vehicle_count.setStyleSheet(
            f"font-size:11px;color:#94a3b8;background:transparent;font-weight:500;")
        sec_row.addWidget(self._vehicle_count)
        left_lay.addLayout(sec_row)


        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._grid_wrap = QWidget(); self._grid_wrap.setStyleSheet("background:#0f172a;")
        self._grid = QGridLayout(self._grid_wrap)
        self._grid.setSpacing(16); self._grid.setContentsMargins(0, 0, 0, 0)
        self._scroll.setWidget(self._grid_wrap)
        left_lay.addWidget(self._scroll, stretch=1)

        # ── Right: booking panel ─────────────────────────────────
        right = QFrame(); right.setObjectName("formPanel")
        right.setFixedWidth(310)
        right.setStyleSheet("background:#ffffff;border-radius:16px;border:1px solid #e2e8f0;")

        form_lay = QVBoxLayout(right)
        form_lay.setContentsMargins(22, 22, 22, 22)
        form_lay.setSpacing(0)

        # Header
        ft = QLabel("Book a Vehicle")
        ft.setStyleSheet(f"font-size:16px;font-weight:800;color:{TEXT_PRIMARY};background:#ffffff;")
        form_lay.addWidget(ft)
        form_lay.addSpacing(4)
        form_sub = QLabel("Fill in your details to reserve")
        form_sub.setStyleSheet(f"font-size:12px;color:{TEXT_MUTED};background:#ffffff;")
        form_lay.addWidget(form_sub)
        form_lay.addSpacing(16)

        # Selected car display
        self.selected_car_label = QLabel("No vehicle selected")
        self.selected_car_label.setWordWrap(True)
        self.selected_car_label.setMinimumHeight(44)
        self.selected_car_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.selected_car_label.setStyleSheet(
            f"background:{GREEN_BG};border-radius:10px;padding:10px 14px;"
            f"font-size:12px;color:{GREEN_DARK};border:1.5px solid {GREEN_BORDER};"
            "font-weight:600;")
        form_lay.addWidget(self.selected_car_label)
        form_lay.addSpacing(16)

        # Form fields
        inp_style = f"background:#f8fafc;border:1.5px solid {BORDER};border-radius:9px;padding:11px 14px;font-size:13px;color:{TEXT_PRIMARY};"
        lbl_style = f"font-size:10px;font-weight:700;color:{TEXT_MUTED};letter-spacing:1px;background:#ffffff;"

        for attr, lbl_txt, ph in [
            ("name_input",    "RENTER NAME",    "Enter full name"),
            ("contact_input", "CONTACT NUMBER", "Phone number"),
            ("street_input",  "STREET",         "House no. & street"),
            ("barangay_input","BARANGAY",       "Barangay"),
            ("city_input",    "CITY",           "City / Municipality"),
        ]:
            fl = QLabel(lbl_txt)
            fl.setStyleSheet(lbl_style)
            form_lay.addWidget(fl); form_lay.addSpacing(5)
            inp = QLineEdit()
            inp.setPlaceholderText(ph); inp.setFixedHeight(44)
            inp.setStyleSheet(inp_style)
            setattr(self, attr, inp)
            form_lay.addWidget(inp); form_lay.addSpacing(12)

        # Start Date
        fl = QLabel("START DATE")
        fl.setStyleSheet(f"font-size:10px;font-weight:700;color:{TEXT_MUTED};letter-spacing:1px;background:#ffffff;")
        form_lay.addWidget(fl); form_lay.addSpacing(5)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setMinimumDate(QDate.currentDate())
        self.start_date_edit.setDisplayFormat("MM/dd/yyyy")
        self.start_date_edit.setFixedHeight(44)
        self.start_date_edit.setStyleSheet(f"""
            QDateEdit {{
                background: #f8fafc;
                border: 1.5px solid {BORDER};
                border-radius: 9px;
                padding: 11px 14px;
                font-size: 13px;
                color: {TEXT_PRIMARY};
            }}
            QDateEdit:focus {{ border: 1.5px solid {GREEN}; background: #ffffff; }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 36px;
                border: none;
                border-left: 1.5px solid {BORDER};
                border-radius: 0 9px 9px 0;
                background: {GREEN};
            }}
            QDateEdit::down-arrow {{
                width: 0px;
                height: 0px;
            }}
            QCalendarWidget QToolButton {{
                background: #ffffff;
                color: {TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 700;
                border: none;
                padding: 6px;
            }}
            QCalendarWidget QToolButton:hover {{ background: {GREEN_BG}; color: {GREEN_DARK}; border-radius: 6px; }}
            QCalendarWidget QMenu {{
                background: #ffffff;
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
            }}
            QCalendarWidget QSpinBox {{
                background: #f8fafc;
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 2px 6px;
                font-size: 13px;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                background: #ffffff;
                color: {TEXT_PRIMARY};
                selection-background-color: {GREEN};
                selection-color: #ffffff;
            }}
            QCalendarWidget QAbstractItemView:disabled {{ color: #cbd5e1; }}
        """)
        form_lay.addWidget(self.start_date_edit)
        form_lay.addSpacing(12)

        # Duration
        fl = QLabel("RENTAL DURATION")
        fl.setStyleSheet(f"font-size:10px;font-weight:700;color:{TEXT_MUTED};letter-spacing:1px;background:#ffffff;")
        form_lay.addWidget(fl); form_lay.addSpacing(5)
        self.duration_combo = QComboBox()
        self.duration_combo.setFixedHeight(44)
        self.duration_combo.setStyleSheet(f"background:#f8fafc;border:1.5px solid {BORDER};border-radius:9px;padding:11px 14px;font-size:13px;color:{TEXT_PRIMARY};")
        self.duration_combo.addItems(["1 Day","3 Days","1 Week","2 Weeks","3 Weeks"])
        self.duration_combo.currentIndexChanged.connect(self._update_total_price)
        form_lay.addWidget(self.duration_combo)
        form_lay.addSpacing(12)

        # Total price — big display
        fl = QLabel("TOTAL PRICE")
        fl.setStyleSheet(f"font-size:10px;font-weight:700;color:{TEXT_MUTED};letter-spacing:1px;background:#ffffff;")
        form_lay.addWidget(fl); form_lay.addSpacing(5)
        self.total_price_input = QLineEdit()
        self.total_price_input.setPlaceholderText("Select a vehicle first")
        self.total_price_input.setFixedHeight(50)
        self.total_price_input.setReadOnly(True)
        self.total_price_input.setStyleSheet(f"background:#f1f5f9;border:1.5px solid {BORDER};border-radius:9px;padding:11px 14px;font-size:14px;font-weight:700;color:{TEXT_MUTED};")
        form_lay.addWidget(self.total_price_input)
        form_lay.addSpacing(16)

        # Rental info box
        info_box = QFrame()
        info_box.setStyleSheet(
            f"QFrame{{background:#f8fafc;border-radius:10px;border:1px solid {BORDER};}}"
        )
        info_lay = QVBoxLayout(info_box); info_lay.setContentsMargins(14,12,14,12); info_lay.setSpacing(8)
        info_title = QLabel("Rental Info")
        info_title.setStyleSheet(f"font-size:11px;font-weight:700;color:{TEXT_PRIMARY};background:#f8fafc;")
        info_lay.addWidget(info_title)
        for note in [
            "Choose your preferred start date",
            "Payment collected upon pickup",
            "Support: (032) 123-4567",
        ]:
            tx = QLabel(note); tx.setStyleSheet(f"background:#f8fafc;font-size:11px;color:{TEXT_MUTED};")
            tx.setWordWrap(True)
            info_lay.addWidget(tx)
        form_lay.addWidget(info_box)
        form_lay.addSpacing(16)

        # Reserve button
        self.rent_button = QPushButton("Reserve Vehicle")
        self.rent_button.setFixedHeight(52)
        self.rent_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rent_button.clicked.connect(self.rent_car)
        self.rent_button.setStyleSheet(
            f"QPushButton{{background:{GREEN};color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:700;padding:14px;}}"
            f"QPushButton:hover{{background:{GREEN_DARK};}}"
            f"QPushButton:pressed{{background:#15803d;}}")
        form_lay.addWidget(self.rent_button)

        body_lay.addWidget(left, stretch=1)
        body_lay.addWidget(right)
        root.addWidget(body, stretch=1)
        self.load_cars()

    def _top_bar(self):
        bar = QWidget(); bar.setObjectName("topBar")
        bar.setFixedHeight(64)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 0, 24, 0)

        # Logo
        logo = QLabel(); logo.setFixedSize(36, 36)
        logo.setStyleSheet("background:transparent;")
        if os.path.exists(self.logo_path):
            px = QPixmap(self.logo_path).scaled(
                36, 36, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(px)
        lay.addWidget(logo); lay.addSpacing(10)

        title = QLabel("Car Rental & Services"); title.setObjectName("appTitle")
        lay.addWidget(title)
        lay.addStretch()

        badge = QLabel("Customer Portal")
        badge.setStyleSheet(
            f"background:{GREEN_BG};border-radius:6px;padding:5px 12px;"
            f"font-size:11px;color:{GREEN_DARK};font-weight:700;"
            f"border:1px solid {GREEN_BORDER};")
        lay.addWidget(badge)
        lay.addSpacing(12)

        lo = QPushButton("Log Out"); lo.setObjectName("logoutBtn")
        lo.setCursor(Qt.CursorShape.PointingHandCursor)
        lo.setFixedHeight(36)
        lo.setStyleSheet(
            "QPushButton{background:transparent;color:#94a3b8;border:1px solid rgba(255,255,255,0.15);"
            "border-radius:8px;font-size:12px;font-weight:600;padding:7px 14px;}"
            "QPushButton:hover{background:rgba(239,68,68,0.12);color:#ef4444;border-color:rgba(239,68,68,0.3);}")
        lo.clicked.connect(self.logout_requested.emit)
        lay.addWidget(lo)
        return bar

    def load_cars(self):
        try:
            import pymysql
            cfg = {"host":"localhost","user":"root","password":"",
                   "database":"se_enterprise",
                   "cursorclass":pymysql.cursors.DictCursor,"connect_timeout":5}
            with pymysql.connect(**cfg) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT car_id, car_name, car_price FROM cars ORDER BY car_id")
                    self.cars_data = cur.fetchall() or []
                    cur.execute("SELECT car_id FROM rentals WHERE status='Pending'")
                    self.rented_car_ids = {r['car_id'] for r in (cur.fetchall() or [])}
            self._render_cards()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_car_cards') and self._car_cards:
            self._render_cards()

    def _render_cards(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._car_cards = {}
        available = self._scroll.viewport().width() - 20
        card_min = 200
        cols = max(2, available // (card_min + 16))
        card_w = (available - (cols - 1) * 16) // cols
        card_h = int(card_w * 0.95)
        rented = getattr(self, 'rented_car_ids', set())
        available_count = sum(1 for c in self.cars_data if c['car_id'] not in rented)
        for i, car in enumerate(self.cars_data):
            is_rented = car['car_id'] in rented
            card = self._car_card(car, int(card_w), int(card_h), is_rented)
            self._car_cards[car["car_id"]] = card
            self._grid.addWidget(card, i // cols, i % cols)
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)
        self._vehicle_count.setText(f"{available_count} vehicles available")

    def _car_card(self, car, card_w=216, card_h=210, is_rented=False):
        card = QFrame(); card.setObjectName("carCard")
        card.setProperty("selected", False)
        card.setFixedSize(card_w, card_h)

        if is_rented:
            card.setStyleSheet(
                f"QFrame{{background:#fff1f2;border-radius:14px;border:2px solid {RED_BORDER};}}"
            )
        else:
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setStyleSheet(
                f"QFrame{{background:#ffffff;border-radius:14px;border:1.5px solid {BORDER};}}"
                f"QFrame:hover{{border:1.5px solid {GREEN};background:#f0fdf4;}}"
            )
            card.mousePressEvent = lambda e, c=car: self._select_car(c)

        lay = QVBoxLayout(card); lay.setContentsMargins(14,12,14,12); lay.setSpacing(3)

        top_row = QHBoxLayout(); top_row.setSpacing(4)
        id_b = QLabel(f"#{car['car_id']}")
        id_b.setFixedHeight(20)
        id_b.setStyleSheet(
            f"background:{GREEN_BG};color:{GREEN_DARK};font-size:10px;font-weight:700;"
            "border-radius:4px;padding:1px 7px;border:none;")
        id_b.setMaximumWidth(38)
        top_row.addWidget(id_b)
        top_row.addStretch()
        if is_rented:
            badge = QLabel("NOT AVAILABLE")
            badge.setFixedHeight(20)
            badge.setStyleSheet(
                f"background:{RED_BG};color:{RED_DARK};font-size:9px;font-weight:700;"
                f"border-radius:4px;padding:1px 7px;border:1px solid {RED_BORDER};")
            top_row.addWidget(badge)

        name = QLabel(str(car['car_name']))
        name.setStyleSheet(
            f"color:{'#9f1239' if is_rented else TEXT_PRIMARY};font-size:13px;font-weight:700;"
            f"background:{'#fff1f2' if is_rented else '#ffffff'};")
        name.setWordWrap(True)
        price = QLabel(f"₱{float(car.get('car_price') or 0):,.0f} / day")
        price.setStyleSheet(
            f"color:{TEXT_MUTED};font-size:11px;font-weight:600;"
            f"background:{'#fff1f2' if is_rented else '#ffffff'};")

        img_h = max(80, card_h - 110)
        img = QLabel(); img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img.setFixedHeight(img_h); img.setStyleSheet("background:transparent;")
        base = os.path.dirname(os.path.abspath(__file__))
        ip = os.path.join(base, "..", "resources", f"{car['car_name']}.jpg")
        if os.path.exists(ip):
            src = QPixmap(ip).scaled(card_w - 28, img_h - 4,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            if is_rented:
                # Tint image red
                tinted = QPixmap(src.size())
                tinted.fill(Qt.GlobalColor.transparent)
                p = QPainter(tinted)
                p.drawPixmap(0, 0, src)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
                p.fillRect(tinted.rect(), QColor(239, 68, 68, 80))
                p.end()
                img.setPixmap(tinted)
            else:
                img.setPixmap(src)

        lay.addLayout(top_row); lay.addWidget(name); lay.addWidget(price)
        lay.addStretch(); lay.addWidget(img); lay.addStretch()
        return card

    def _select_car(self, car):
        self.selected_car = car
        for cid, card in self._car_cards.items():
            sel = cid == car["car_id"]
            card.setProperty("selected", sel)
            card.style().unpolish(card); card.style().polish(card)
        self.selected_car_label.setText(
            f"✓  {car['car_name']}  ·  ₱{float(car['car_price']):,.0f}/day")
        self._update_total_price()

    def prefill(self, customer: dict, car: dict = None):
        """Pre-fill form fields for a returning customer."""
        addr = customer.get('complete_address', '')
        parts = [p.strip() for p in addr.split(',')]
        self.name_input.setText(customer.get('customer_name', ''))
        self.contact_input.setText(customer.get('contact_number', ''))
        self.street_input.setText(parts[0] if len(parts) > 0 else '')
        self.barangay_input.setText(parts[1] if len(parts) > 1 else '')
        self.city_input.setText(parts[2] if len(parts) > 2 else '')
        if car:
            # Find and select the matching car card
            for c in self.cars_data:
                if c['car_id'] == car['car_id']:
                    self._select_car(c)
                    break

    def _multiplier(self, d):
        return {"1 Day":1, "3 Days":3, "1 Week":7, "2 Weeks":14, "3 Weeks":21}.get(d, 1)

    def _update_total_price(self):
        if not self.selected_car:
            self.total_price_input.setText(""); return
        m = self._multiplier(self.duration_combo.currentText())
        total = float(self.selected_car.get("car_price") or 0) * m
        self.total_price_input.setText(f"₱ {total:,.2f}")

    def rent_car(self):
        try:
            if not self.selected_car:
                QMessageBox.warning(self, "No Vehicle Selected", "Please select a vehicle."); return
            if self.selected_car['car_id'] in getattr(self, 'rented_car_ids', set()):
                QMessageBox.warning(self, "Not Available", "This vehicle is already rented."); return

            name     = self.name_input.text().strip()
            contact  = self.contact_input.text().strip()
            street   = self.street_input.text().strip()
            barangay = self.barangay_input.text().strip()
            city     = self.city_input.text().strip()

            if not name or not contact:
                QMessageBox.warning(self, "Missing Info", "Please enter your name and contact number."); return
            if not street or not barangay or not city:
                QMessageBox.warning(self, "Missing Address", "Please fill in Street, Barangay, and City."); return

            complete_address = f"{street}, {barangay}, {city}"
            car_price  = float(self.selected_car['car_price'])
            duration   = self.duration_combo.currentText()
            total      = car_price * self._multiplier(duration)
            qd         = self.start_date_edit.date()
            start_date = date(qd.year(), qd.month(), qd.day())

            import pymysql
            cfg = {"host":"localhost","user":"root","password":"",
                   "database":"se_enterprise",
                   "cursorclass":pymysql.cursors.DictCursor,"connect_timeout":5}
            with pymysql.connect(**cfg) as conn:
                with conn.cursor() as cur:
                    # One car per person — block if customer already has any Pending rental
                    cur.execute("""
                        SELECT r.rental_id, ca.car_name FROM rentals r
                        JOIN customers c ON r.customer_id = c.customer_id
                        JOIN cars ca ON r.car_id = ca.car_id
                        WHERE c.customer_name = %s AND r.status = 'Pending'
                    """, (name,))
                    active = cur.fetchone()
                    if active:
                        QMessageBox.warning(self, "Already Renting",
                            f"'{name}' already has an active rental for '{active['car_name']}'.\n"
                            "Please return the current car before renting another.")
                        return

                    # Upsert customer — match by name, update address & contact
                    cur.execute("SELECT customer_id FROM customers WHERE customer_name=%s", (name,))
                    cust = cur.fetchone()
                    if cust is None:
                        cur.execute(
                            "INSERT INTO customers (customer_name, contact_number, complete_address) VALUES (%s,%s,%s)",
                            (name, contact, complete_address))
                        cid = conn.insert_id()
                    else:
                        cid = cust['customer_id']
                        cur.execute(
                            "UPDATE customers SET contact_number=%s, complete_address=%s WHERE customer_id=%s",
                            (contact, complete_address, cid))

                    cur.execute(
                        "INSERT INTO rentals (car_id,customer_id,total_price,date_rented,status) VALUES (%s,%s,%s,%s,%s)",
                        (self.selected_car['car_id'], cid, total, start_date, "Pending"))
                    rid = cur.lastrowid
                    conn.commit()

            car_snapshot = dict(self.selected_car)
            self.load_cars()
            dlg = RentalDetailWindow(
                rental_id=rid, customer_name=name, contact=contact,
                address=complete_address, car=car_snapshot,
                duration=duration, total=total, start_date=start_date, parent=self)
            if dlg.exec() and dlg.done_clicked:
                self.rental_confirmed.emit({
                    'rental_id': rid, 'customer_name': name, 'contact': contact,
                    'address': complete_address, 'car': car_snapshot,
                    'duration': duration, 'total': total, 'start_date': start_date
                })
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))



class RentalDetailWindow(QDialog):
    """Window shown after a successful rental — shows details + Cancel/Return + Extend."""

    DURATION_DAYS = {"1 Day": 1, "3 Days": 3, "1 Week": 7, "2 Weeks": 14, "3 Weeks": 21}

    def __init__(self, rental_id, customer_name, contact, address, car, duration, total, start_date, parent=None):
        super().__init__(parent)
        self.done_clicked  = False
        self.rental_id     = rental_id
        self.customer_name = customer_name
        self.contact       = contact
        self.address       = address
        self.car           = car
        self.duration      = duration
        self.total         = total
        self.start_date    = start_date
        self.setWindowTitle("Rental Details")
        self.setMinimumWidth(520)
        self.setStyleSheet("background:#fff; font-family:'Segoe UI';")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(0)

        # ── Header ──────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("Rental Details")
        title.setStyleSheet(f"font-size:20px;font-weight:800;color:{TEXT_PRIMARY};background:transparent;")
        hdr.addWidget(title); hdr.addStretch()
        badge = QLabel(f"#{self.rental_id}")
        badge.setStyleSheet(
            f"background:{GREEN_BG};color:{GREEN_DARK};border-radius:8px;"
            "padding:6px 12px;font-size:14px;font-weight:700;border:none;")
        hdr.addWidget(badge)
        lay.addLayout(hdr)
        lay.addSpacing(4)
        sub = QLabel("SE Enterprise Car Rental & Services")
        sub.setStyleSheet(f"font-size:12px;color:{TEXT_MUTED};background:transparent;")
        lay.addWidget(sub)
        lay.addSpacing(18)

        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color:{BORDER};"); lay.addWidget(div)
        lay.addSpacing(18)

        # ── Car image + info side by side ────────────────────────
        car_row = QHBoxLayout(); car_row.setSpacing(18)

        img_lbl = QLabel(); img_lbl.setFixedSize(160, 110)
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_lbl.setStyleSheet(f"background:#f8fafc;border-radius:10px;border:1px solid {BORDER};")
        base = os.path.dirname(os.path.abspath(__file__))
        ip = os.path.join(base, "..", "resources", f"{self.car['car_name']}.jpg")
        if os.path.exists(ip):
            px = QPixmap(ip).scaled(156, 106, Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
            img_lbl.setPixmap(px)
        car_row.addWidget(img_lbl)

        info_col = QVBoxLayout(); info_col.setSpacing(6)
        car_name_lbl = QLabel(self.car['car_name'])
        car_name_lbl.setStyleSheet(f"font-size:18px;font-weight:800;color:{TEXT_PRIMARY};background:transparent;")
        info_col.addWidget(car_name_lbl)
        price_lbl = QLabel(f"₱{float(self.car['car_price']):,.0f} / day")
        price_lbl.setStyleSheet(f"font-size:13px;color:{TEXT_MUTED};background:transparent;")
        info_col.addWidget(price_lbl)
        info_col.addStretch()
        status_pill = QLabel("● Active Rental")
        status_pill.setStyleSheet(
            f"background:{GREEN_BG};color:{GREEN_DARK};border-radius:8px;"
            "padding:5px 12px;font-size:12px;font-weight:700;border:none;")
        info_col.addWidget(status_pill)
        car_row.addLayout(info_col)
        lay.addLayout(car_row)
        lay.addSpacing(18)

        div2 = QFrame(); div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet(f"color:{BORDER};"); lay.addWidget(div2)
        lay.addSpacing(16)

        # ── Rental details rows ──────────────────────────────────
        days = self.DURATION_DAYS.get(self.duration, 1)
        from datetime import timedelta
        end_date = self.start_date + timedelta(days=days)

        details = [
            ("Renter",      self.customer_name),
            ("Contact",     self.contact),
            ("Address",     self.address),
            ("Start Date",  self.start_date.strftime("%B %d, %Y")),
            ("End Date",    end_date.strftime("%B %d, %Y")),
            ("Duration",    self.duration),
            ("Total",       f"₱ {self.total:,.2f}"),
        ]
        for lbl, val in details:
            r = QHBoxLayout(); r.setContentsMargins(0, 0, 0, 0)
            l = QLabel(lbl)
            l.setStyleSheet(f"font-size:12px;color:{TEXT_MUTED};font-weight:600;min-width:90px;background:transparent;")
            is_total = lbl == "Total"
            v = QLabel(val)
            v.setWordWrap(True)
            v.setStyleSheet(
                f"font-size:{'17px' if is_total else '13px'};"
                f"color:{GREEN_DARK if is_total else TEXT_PRIMARY};"
                f"font-weight:{'800' if is_total else '600'};"
                "background:transparent;")
            r.addWidget(l); r.addStretch(); r.addWidget(v)
            lay.addLayout(r); lay.addSpacing(8)

        lay.addSpacing(10)
        div3 = QFrame(); div3.setFrameShape(QFrame.Shape.HLine)
        div3.setStyleSheet(f"color:{BORDER};"); lay.addWidget(div3)
        lay.addSpacing(20)

        # ── Done button ──────────────────────────────────────────
        done_btn = QPushButton("Done")
        done_btn.setFixedHeight(46)
        done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        done_btn.setStyleSheet(
            f"QPushButton{{background:{GREEN};color:#fff;border:none;"
            "border-radius:10px;font-size:15px;font-weight:700;padding:0 20px;}}"
            f"QPushButton:hover{{background:{GREEN_DARK};}}")
        done_btn.clicked.connect(self._on_done)
        lay.addWidget(done_btn)

    def _on_done(self):
        self.done_clicked = True
        self.accept()

    def _cancel_rental(self):
        reply = QMessageBox.question(
            self, "Cancel / Return",
            "Are you sure you want to cancel/return this rental?\nStatus will be set to 'Returned'.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            import pymysql
            cfg = {"host": "localhost", "user": "root", "password": "",
                   "database": "se_enterprise",
                   "cursorclass": pymysql.cursors.DictCursor, "connect_timeout": 5}
            with pymysql.connect(**cfg) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE rentals SET status='Returned', date_returned=%s WHERE rental_id=%s",
                        (date.today(), self.rental_id))
                    conn.commit()
            QMessageBox.information(self, "Done", "Rental has been returned successfully.")
            # Refresh parent car grid
            if self.parent() and hasattr(self.parent(), 'load_cars'):
                self.parent().load_cars()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _extend_rental(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Extend Rental")
        dlg.setFixedWidth(360)
        dlg.setStyleSheet("background:#fff; font-family:'Segoe UI';")
        lay = QVBoxLayout(dlg); lay.setContentsMargins(28, 24, 28, 24); lay.setSpacing(12)

        title = QLabel("Extend Rental")
        title.setStyleSheet(f"font-size:16px;font-weight:800;color:{TEXT_PRIMARY};background:transparent;")
        lay.addWidget(title)

        lbl = QLabel("Additional duration:")
        lbl.setStyleSheet(f"font-size:12px;color:{TEXT_MUTED};background:transparent;")
        lay.addWidget(lbl)

        combo = QComboBox(); combo.setFixedHeight(44)
        combo.setStyleSheet(
            f"QComboBox{{background:#f8fafc;border:1.5px solid {BORDER};border-radius:9px;"
            f"padding:11px 14px;font-size:13px;color:{TEXT_PRIMARY};}}"
            f"QComboBox::drop-down{{border:none;width:28px;}}")
        combo.addItems(["1 Day", "3 Days", "1 Week", "2 Weeks", "3 Weeks"])
        lay.addWidget(combo)

        extra_lbl = QLabel("")
        extra_lbl.setStyleSheet(f"font-size:13px;font-weight:700;color:{GREEN_DARK};background:transparent;")
        lay.addWidget(extra_lbl)

        def update_extra():
            days = self.DURATION_DAYS.get(combo.currentText(), 1)
            extra = float(self.car['car_price']) * days
            extra_lbl.setText(f"Additional charge: ₱ {extra:,.2f}")

        combo.currentIndexChanged.connect(update_extra)
        update_extra()

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        cancel = QPushButton("Cancel"); cancel.setFixedHeight(42)
        cancel.setStyleSheet(
            f"QPushButton{{background:#f1f5f9;color:{TEXT_PRIMARY};border-radius:9px;"
            f"font-weight:600;font-size:13px;border:1px solid {BORDER};}}"
            f"QPushButton:hover{{background:#e2e8f0;}}")
        confirm = QPushButton("Confirm Extension"); confirm.setFixedHeight(42)
        confirm.setStyleSheet(
            f"QPushButton{{background:{GREEN};color:#fff;border-radius:9px;"
            "font-weight:700;font-size:13px;border:none;}}"
            f"QPushButton:hover{{background:{GREEN_DARK};}}")
        btn_row.addWidget(cancel); btn_row.addWidget(confirm)
        lay.addLayout(btn_row)

        cancel.clicked.connect(dlg.reject)

        def do_extend():
            days = self.DURATION_DAYS.get(combo.currentText(), 1)
            extra = float(self.car['car_price']) * days
            try:
                import pymysql
                cfg = {"host": "localhost", "user": "root", "password": "",
                       "database": "se_enterprise",
                       "cursorclass": pymysql.cursors.DictCursor, "connect_timeout": 5}
                with pymysql.connect(**cfg) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE rentals SET total_price = total_price + %s WHERE rental_id = %s",
                            (extra, self.rental_id))
                        conn.commit()
                self.total += extra
                QMessageBox.information(dlg, "Extended",
                    f"Rental extended by {combo.currentText()}.\nNew total: ₱ {self.total:,.2f}")
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(dlg, "Error", str(e))

        confirm.clicked.connect(do_extend)
        dlg.exec()
