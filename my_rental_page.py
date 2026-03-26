from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QDialog, QComboBox, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from datetime import date, timedelta
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
BORDER       = "#e2e8f0"
TEXT_PRIMARY = "#0f172a"
TEXT_MUTED   = "#64748b"

DURATION_DAYS = {"1 Day": 1, "3 Days": 3, "1 Week": 7, "2 Weeks": 14, "3 Weeks": 21}


def _msg(parent, kind, title, text):
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setStyleSheet("QMessageBox{background:#ffffff;} QLabel{color:#0f172a;background:#ffffff;} QPushButton{background:#f1f5f9;color:#0f172a;border:1px solid #e2e8f0;border-radius:7px;padding:6px 18px;font-weight:600;} QPushButton:hover{background:#e2e8f0;}")
    if kind == "info":
        mb.setIcon(QMessageBox.Icon.Information)
    elif kind == "warn":
        mb.setIcon(QMessageBox.Icon.Warning)
    elif kind == "crit":
        mb.setIcon(QMessageBox.Icon.Critical)
    elif kind == "question":
        mb.setIcon(QMessageBox.Icon.Question)
        mb.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    mb.exec()
    return mb.result()


class MyRentalPage(QWidget):
    back_requested   = pyqtSignal()
    logout_requested = pyqtSignal()
    rent_again       = pyqtSignal(dict, dict)
    rent_another     = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.rental_info   = {}
        self.customer_info = {}
        self.rentals_list  = []
        self._mode = "new"   # "new" = post-reservation, "returning" = history
        self.setStyleSheet("background:#0f172a; font-family:'Segoe UI';")
        self._build()

    # ── Public loaders ───────────────────────────────────────────
    def load_rental(self, info: dict):
        """Called after a fresh reservation (Done button)."""
        self._mode = "new"
        self.rental_info = info
        self._renter_name_lbl.setText(info.get('customer_name', ''))
        self._renter_id_badge.setText(f"#{info.get('rental_id', '')}")
        self._renter_id_badge.show()
        self._refresh()

    def load_returning(self, customer: dict, rentals: list):
        """Called for a returning customer lookup."""
        self._mode = "returning"
        self.customer_info = customer
        self.rentals_list  = rentals
        self._renter_name_lbl.setText(customer.get('customer_name', ''))
        self._renter_id_badge.setText(f"ID #{customer.get('customer_id', '')}")
        self._renter_id_badge.show()
        self._refresh()

    # ── Layout skeleton ──────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._top_bar())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#0f172a;}"
                             "QScrollBar:vertical{background:transparent;width:5px;border-radius:3px;}"
                             "QScrollBar::handle:vertical{background:#334155;border-radius:3px;min-height:20px;}"
                             "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;}")

        self._body = QWidget()
        self._body.setStyleSheet("background:#0f172a;")
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(40, 32, 40, 32)
        self._body_lay.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self._body_lay.setSpacing(20)

        scroll.setWidget(self._body)
        root.addWidget(scroll, stretch=1)

    def _top_bar(self):
        bar = QWidget()
        bar.setFixedHeight(64)
        bar.setStyleSheet("background:#0f172a; border-bottom:1px solid rgba(255,255,255,0.08);")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 0, 24, 0)

        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources", "SE.jpg")
        logo = QLabel(); logo.setFixedSize(36, 36)
        logo.setStyleSheet("background:transparent;")
        if os.path.exists(logo_path):
            px = QPixmap(logo_path).scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(px)
        lay.addWidget(logo); lay.addSpacing(10)

        title = QLabel("Car Rental & Services")
        title.setStyleSheet("font-size:17px;font-weight:700;color:#f1f5f9;background:transparent;")
        lay.addWidget(title)
        lay.addSpacing(16)

        # Renter name + ID badge (updated when data loads)
        self._renter_name_lbl = QLabel("")
        self._renter_name_lbl.setStyleSheet("font-size:13px;font-weight:600;color:#e2e8f0;background:transparent;")
        self._renter_id_badge = QLabel("")
        self._renter_id_badge.setStyleSheet(
            f"background:{GREEN_BG};color:{GREEN_DARK};border-radius:6px;"
            "padding:4px 10px;font-size:11px;font-weight:700;border:none;")
        self._renter_id_badge.hide()
        lay.addWidget(self._renter_name_lbl)
        lay.addSpacing(8)
        lay.addWidget(self._renter_id_badge)
        lay.addStretch()

        back_btn = QPushButton("← Back")
        back_btn.setFixedHeight(36)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#94a3b8;border:1px solid rgba(255,255,255,0.15);"
            "border-radius:8px;font-size:12px;font-weight:600;padding:7px 14px;}"
            "QPushButton:hover{background:rgba(255,255,255,0.08);color:#f1f5f9;}")
        back_btn.clicked.connect(self.back_requested.emit)
        lay.addWidget(back_btn)
        lay.addSpacing(8)

        logout_btn = QPushButton("Log Out")
        logout_btn.setFixedHeight(36)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#94a3b8;border:1px solid rgba(255,255,255,0.15);"
            "border-radius:8px;font-size:12px;font-weight:600;padding:7px 14px;}"
            "QPushButton:hover{background:rgba(239,68,68,0.12);color:#ef4444;border-color:rgba(239,68,68,0.3);}")
        logout_btn.clicked.connect(self.logout_requested.emit)
        lay.addWidget(logout_btn)
        return bar

    # ── Refresh dispatcher ───────────────────────────────────────
    def _clear_body(self):
        while self._body_lay.count():
            item = self._body_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _refresh(self):
        self._clear_body()
        if self._mode == "new":
            self._render_new_rental()
        else:
            self._render_history()

    # ── Mode: new rental (post-reservation) ─────────────────────
    def _render_new_rental(self):
        info = self.rental_info
        if not info:
            return
        card = self._make_card()
        lay  = card.layout()
        days = DURATION_DAYS.get(info['duration'], 1)
        end_date = info['start_date'] + timedelta(days=days)

        self._add_card_header(lay, f"#{info['rental_id']}", "My Rental")
        self._add_car_row(lay, info['car'], "● Active Rental", GREEN_BG, GREEN_DARK)
        self._add_divider(lay)

        self._total_lbl = None
        rows = [
            ("Renter",     info['customer_name']),
            ("Contact",    info['contact']),
            ("Address",    info['address']),
            ("Start Date", info['start_date'].strftime("%B %d, %Y")),
            ("End Date",   end_date.strftime("%B %d, %Y")),
            ("Duration",   info['duration']),
            ("Total",      f"₱ {info['total']:,.2f}"),
        ]
        for lbl_txt, val in rows:
            is_total = lbl_txt == "Total"
            v = self._add_detail_row(lay, lbl_txt, val, is_total)
            if is_total:
                self._total_lbl = v

        self._add_divider(lay)
        lay.addSpacing(4)

        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        cancel_btn = self._action_btn("Cancel / Return", RED_BG, "#fecaca", RED_DARK, f"1.5px solid {RED_BORDER}")
        cancel_btn.clicked.connect(self._cancel_rental)
        extend_btn = self._action_btn("Extend Rental", GREEN, GREEN_DARK)
        extend_btn.clicked.connect(self._extend_rental)
        btn_row.addWidget(cancel_btn); btn_row.addStretch(); btn_row.addWidget(extend_btn)
        lay.addLayout(btn_row)

        self._body_lay.addWidget(card)

    # ── Mode: returning customer history ────────────────────────
    def _render_history(self):
        c = self.customer_info
        rentals = self.rentals_list

        # Customer info card
        info_card = self._make_card(width=620)
        ilay = info_card.layout()
        hdr = QHBoxLayout()
        t = QLabel("Rental History")
        t.setStyleSheet(f"font-size:20px;font-weight:800;color:{TEXT_PRIMARY};background:transparent;")
        hdr.addWidget(t); hdr.addStretch()
        badge = QLabel(f"ID #{c['customer_id']}")
        badge.setStyleSheet(
            f"background:{GREEN_BG};color:{GREEN_DARK};border-radius:8px;"
            "padding:6px 12px;font-size:13px;font-weight:700;border:none;")
        hdr.addWidget(badge)
        ilay.addLayout(hdr)
        ilay.addSpacing(4)
        sub = QLabel(f"{c['customer_name']}  ·  {c.get('contact_number','')}")
        sub.setStyleSheet(f"font-size:13px;color:{TEXT_MUTED};background:transparent;")
        ilay.addWidget(sub)
        self._body_lay.addWidget(info_card)

        if not rentals:
            empty = QLabel("No rental records found.")
            empty.setStyleSheet(f"font-size:14px;color:#94a3b8;background:transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._body_lay.addWidget(empty)
            return

        last_rental = rentals[0]
        last_returned = last_rental.get('status') == 'Returned'

        for rental in rentals:
            self._body_lay.addWidget(self._rental_history_card(rental, last_rental, last_returned))

    def _rental_history_card(self, rental, last_rental, last_returned):
        is_last = rental['rental_id'] == last_rental['rental_id']
        card = self._make_card(width=620)
        lay  = card.layout()

        status = rental.get('status', '')
        is_active  = status == 'Pending'
        pill_bg    = GREEN_BG   if is_active else "#f1f5f9"
        pill_color = GREEN_DARK if is_active else TEXT_MUTED
        pill_text  = "● Active" if is_active else f"✓ {status}"

        self._add_card_header(lay, f"#{rental['rental_id']}", rental['car_name'], pill_bg, pill_color, pill_text)

        base = os.path.dirname(os.path.abspath(__file__))
        ip   = os.path.join(base, "..", "resources", f"{rental['car_name']}.jpg")
        car_dict = {'car_name': rental['car_name'], 'car_price': rental['car_price']}
        self._add_car_row(lay, car_dict, pill_text, pill_bg, pill_color)
        self._add_divider(lay)

        start = rental.get('date_rented')
        end   = rental.get('date_returned')
        rows  = [
            ("Status",     status),
            ("Start Date", start.strftime("%B %d, %Y") if start else "—"),
            ("Returned",   end.strftime("%B %d, %Y") if end else "—"),
            ("Total",      f"₱ {float(rental.get('total_price') or 0):,.2f}"),
        ]
        for lbl_txt, val in rows:
            self._add_detail_row(lay, lbl_txt, val, lbl_txt == "Total")

        # Buttons only on the most recent rental
        if is_last:
            self._add_divider(lay)
            lay.addSpacing(4)
            btn_row = QHBoxLayout(); btn_row.setSpacing(10)

            if not last_returned:
                # Still active — show Return button
                return_btn = self._action_btn("Return Car", RED_BG, "#fecaca", RED_DARK, f"1.5px solid {RED_BORDER}")
                return_btn.clicked.connect(lambda _, r=rental: self._return_car(r))
                btn_row.addWidget(return_btn)
            else:
                # Already returned — show Rent Again + Rent Another
                again_btn = self._action_btn("Rent Again", GREEN, GREEN_DARK)
                again_btn.clicked.connect(lambda: self._on_rent_again(rental))
                another_btn = self._action_btn("Rent Another", "#f8fafc", "#f1f5f9", TEXT_PRIMARY, f"1.5px solid {BORDER}")
                another_btn.clicked.connect(self._on_rent_another)
                btn_row.addWidget(again_btn)
                btn_row.addStretch()
                btn_row.addWidget(another_btn)

            lay.addLayout(btn_row)

        return card

    def _on_rent_again(self, rental):
        c = self.customer_info
        car = {'car_id': rental['car_id'], 'car_name': rental['car_name'], 'car_price': rental['car_price']}
        self.rent_again.emit(dict(c), car)

    def _on_rent_another(self):
        self.rent_another.emit(dict(self.customer_info))

    # ── Shared helpers ───────────────────────────────────────────
    def _make_card(self, width=560):
        card = QFrame()
        card.setStyleSheet("QFrame{background:#ffffff;border-radius:18px;border:1px solid #e2e8f0;}")
        card.setFixedWidth(width)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(0)
        return card

    def _add_card_header(self, lay, badge_text, title_text,
                         pill_bg=None, pill_color=None, pill_text=None):
        hdr = QHBoxLayout()
        title = QLabel(title_text)
        title.setStyleSheet(f"font-size:18px;font-weight:800;color:{TEXT_PRIMARY};background:transparent;")
        hdr.addWidget(title); hdr.addStretch()
        badge = QLabel(badge_text)
        badge.setStyleSheet(
            f"background:{GREEN_BG};color:{GREEN_DARK};border-radius:8px;"
            "padding:5px 10px;font-size:13px;font-weight:700;border:none;")
        hdr.addWidget(badge)
        lay.addLayout(hdr)
        lay.addSpacing(4)
        sub = QLabel("SE Enterprise Car Rental & Services")
        sub.setStyleSheet(f"font-size:11px;color:{TEXT_MUTED};background:transparent;")
        lay.addWidget(sub)
        lay.addSpacing(14)
        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color:{BORDER};"); lay.addWidget(div)
        lay.addSpacing(14)

    def _add_car_row(self, lay, car, pill_text, pill_bg, pill_color):
        car_row = QHBoxLayout(); car_row.setSpacing(16)
        img_lbl = QLabel(); img_lbl.setFixedSize(140, 96)
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_lbl.setStyleSheet(f"background:#f8fafc;border-radius:10px;border:1px solid {BORDER};")
        base = os.path.dirname(os.path.abspath(__file__))
        ip = os.path.join(base, "..", "resources", f"{car['car_name']}.jpg")
        if os.path.exists(ip):
            px = QPixmap(ip).scaled(136, 92, Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
            img_lbl.setPixmap(px)
        car_row.addWidget(img_lbl)

        col = QVBoxLayout(); col.setSpacing(4)
        n = QLabel(car['car_name'])
        n.setStyleSheet(f"font-size:16px;font-weight:800;color:{TEXT_PRIMARY};background:transparent;")
        col.addWidget(n)
        p = QLabel(f"₱{float(car['car_price']):,.0f} / day")
        p.setStyleSheet(f"font-size:12px;color:{TEXT_MUTED};background:transparent;")
        col.addWidget(p)
        col.addStretch()
        pill = QLabel(pill_text)
        pill.setStyleSheet(
            f"background:{pill_bg};color:{pill_color};border-radius:7px;"
            "padding:4px 10px;font-size:11px;font-weight:700;border:none;")
        col.addWidget(pill)
        car_row.addLayout(col)
        lay.addLayout(car_row)
        lay.addSpacing(14)

    def _add_divider(self, lay):
        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color:{BORDER};"); lay.addWidget(div)
        lay.addSpacing(12)

    def _add_detail_row(self, lay, label, value, is_total=False):
        r = QHBoxLayout(); r.setContentsMargins(0, 0, 0, 0)
        l = QLabel(label)
        l.setStyleSheet(f"font-size:12px;color:{TEXT_MUTED};font-weight:600;min-width:90px;background:transparent;")
        v = QLabel(value); v.setWordWrap(True)
        v.setStyleSheet(
            f"font-size:{'16px' if is_total else '13px'};"
            f"color:{GREEN_DARK if is_total else TEXT_PRIMARY};"
            f"font-weight:{'800' if is_total else '600'};"
            "background:transparent;")
        r.addWidget(l); r.addStretch(); r.addWidget(v)
        lay.addLayout(r); lay.addSpacing(7)
        return v

    def _action_btn(self, text, bg, hover, color="#fff", border="none"):
        btn = QPushButton(text)
        btn.setFixedHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton{{background:{bg};color:{color};border:{border};"
            "border-radius:10px;font-size:14px;font-weight:700;padding:0 20px;}}"
            f"QPushButton:hover{{background:{hover};}}")
        return btn

    # ── Cancel / Extend (new rental mode) ───────────────────────
    def _return_car(self, rental):
        reply = _msg(self, "question", "Return Car",
            f"Are you sure you want to return '{rental['car_name']}'?")
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
                        (date.today(), rental['rental_id']))
                    conn.commit()
            _msg(self, "info", "Returned", "Car returned successfully.")
            try:
                with pymysql.connect(**cfg) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT r.rental_id, ca.car_id, ca.car_name, ca.car_price,
                                   r.total_price, r.date_rented, r.date_returned, r.status
                            FROM rentals r JOIN cars ca ON r.car_id=ca.car_id
                            WHERE r.customer_id=%s ORDER BY r.rental_id DESC
                        """, (self.customer_info['customer_id'],))
                        self.rentals_list = cur.fetchall() or []
            except Exception:
                pass
            self._refresh()
        except Exception as e:
            _msg(self, "crit", "Error", str(e))

    def _cancel_rental(self):
        reply = _msg(self, "question", "Cancel / Return",
            "Are you sure you want to cancel/return this rental?\nStatus will be set to 'Returned'.")
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
                        (date.today(), self.rental_info['rental_id']))
                    conn.commit()
            _msg(self, "info", "Done", "Rental has been returned successfully.")
            self.back_requested.emit()
        except Exception as e:
            _msg(self, "crit", "Error", str(e))

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
            days = DURATION_DAYS.get(combo.currentText(), 1)
            extra = float(self.rental_info['car']['car_price']) * days
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
            days = DURATION_DAYS.get(combo.currentText(), 1)
            extra = float(self.rental_info['car']['car_price']) * days
            try:
                import pymysql
                cfg = {"host": "localhost", "user": "root", "password": "",
                       "database": "se_enterprise",
                       "cursorclass": pymysql.cursors.DictCursor, "connect_timeout": 5}
                with pymysql.connect(**cfg) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE rentals SET total_price = total_price + %s WHERE rental_id = %s",
                            (extra, self.rental_info['rental_id']))
                        conn.commit()
                self.rental_info['total'] += extra
                if self._total_lbl:
                    self._total_lbl.setText(f"₱ {self.rental_info['total']:,.2f}")
                _msg(self, "info", "Extended",
                    f"Rental extended by {combo.currentText()}.\nNew total: ₱ {self.rental_info['total']:,.2f}")
                dlg.accept()
            except Exception as e:
                _msg(self, "crit", "Error", str(e))

        confirm.clicked.connect(do_extend)
        dlg.exec()
