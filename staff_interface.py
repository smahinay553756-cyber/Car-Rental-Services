import os, sys, tempfile, shutil
from datetime import datetime, date

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QSize
from PyQt6.QtGui import QColor, QImage, QPixmap, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QGridLayout, QStackedWidget, QScrollArea, QGraphicsDropShadowEffect,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox,
    QApplication, QMainWindow, QDialog, QSizePolicy, QFileDialog, QDoubleSpinBox
)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors as rl_colors

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "..", "resources", "SE.jpg")
RES_DIR   = os.path.join(BASE_DIR, "..", "resources")

GREEN        = "#22c55e"
GREEN_DARK   = "#16a34a"
GREEN_BG     = "#dcfce7"
GREEN_BORDER = "#bbf7d0"
RED          = "#ef4444"
RED_BG       = "#fee2e2"
RED_BORDER   = "#fecaca"
SIDEBAR_BG   = "#0f172a"
CONTENT_BG   = "#f8fafc"
CARD_BG      = "#ffffff"
BORDER       = "#e2e8f0"
TEXT_PRIMARY = "#0f172a"
TEXT_MUTED   = "#64748b"
BLUE_BG      = "#eff6ff"
AMBER_BG     = "#fffbeb"

SCROLLBAR = """
QScrollBar:vertical   { background:transparent; width:5px; border-radius:3px; margin:0; }
QScrollBar::handle:vertical   { background:#cbd5e1; border-radius:3px; min-height:24px; }
QScrollBar::handle:vertical:hover { background:#94a3b8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0px; }
QScrollBar:horizontal { background:transparent; height:5px; }
QScrollBar::handle:horizontal { background:#cbd5e1; border-radius:3px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0px; }
"""

NAV_BTN = f"""
QPushButton {{
    background: transparent; color: #94a3b8;
    text-align: left; padding: 11px 18px;
    font-size: 13px; font-weight: 500;
    border: none; border-radius: 8px; margin: 1px 8px;
}}
QPushButton:hover {{ background: rgba(255,255,255,0.08); color: #e2e8f0; }}
QPushButton:checked {{
    background: rgba(34,197,94,0.15); color: {GREEN};
    font-weight: 700; border: 1px solid rgba(34,197,94,0.25);
}}
"""

TABLE_STYLE = f"""
QTableWidget {{
    background: {CARD_BG}; border: none;
    color: {TEXT_PRIMARY}; font-size: 13px;
    alternate-background-color: #f8fafc;
    gridline-color: transparent; outline: none;
}}
QHeaderView::section {{
    background: #f8fafc; padding: 13px 12px;
    border: none; border-bottom: 2px solid {BORDER};
    font-weight: 700; color: {TEXT_MUTED};
    font-size: 11px; letter-spacing: 0.8px;
}}
QTableWidget::item {{ padding: 12px 12px; border-bottom: 1px solid #f1f5f9; }}
QTableWidget::item:selected {{ background: #f0fdf4; color: {TEXT_PRIMARY}; }}
"""

EXPORT_BTN = f"""
QPushButton {{
    background: {GREEN}; color: #fff;
    padding: 0 22px; border-radius: 9px;
    font-weight: 700; font-size: 13px; border: none;
}}
QPushButton:hover {{ background: {GREEN_DARK}; }}
"""

SEARCH_INPUT = f"""
QLineEdit {{
    background: {CARD_BG}; border: 1.5px solid {BORDER};
    border-radius: 9px; padding: 10px 16px;
    font-size: 13px; color: {TEXT_PRIMARY};
}}
QLineEdit:focus {{ border: 1.5px solid {GREEN}; }}
"""

ADD_INPUT = f"""
QLineEdit {{
    background: #f8fafc; border: 1.5px solid {BORDER};
    border-radius: 8px; padding: 10px 13px;
    font-size: 13px; color: {TEXT_PRIMARY};
}}
QLineEdit:focus {{ border: 1.5px solid {GREEN}; background: #fff; }}
"""


# ── DB ────────────────────────────────────────────────────────────
def _db_query(sql, params=None):
    try:
        import pymysql
        cfg = {"host":"localhost","user":"root","password":"",
               "database":"se_enterprise",
               "cursorclass":pymysql.cursors.DictCursor,"connect_timeout":5}
        with pymysql.connect(**cfg) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                return cur.fetchall()
    except Exception as e:
        print(f"[DB] {e}"); return []

def _db_exec(sql, params=None):
    try:
        import pymysql
        cfg = {"host":"localhost","user":"root","password":"",
               "database":"se_enterprise",
               "cursorclass":pymysql.cursors.DictCursor,"connect_timeout":5}
        with pymysql.connect(**cfg) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                last_id = cur.lastrowid
                conn.commit()
                return last_id
    except Exception as e:
        print(f"[DB EXEC] {e}"); return None


# ── PDF Service ───────────────────────────────────────────────────
class PdfService:
    def _header(self, el, title, name):
        s = getSampleStyleSheet()
        el.append(Paragraph(title, s['h1']))
        el.append(Paragraph(
            f"Exported by: {name} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", s['Normal']))
        el.append(Spacer(1, 0.25*inch))

    def generate_earnings_report(self, staff_name, line_path, bar_path):
        fp = f"Earning_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(fp, pagesize=(11*inch, 8.5*inch))
        el, s = [], getSampleStyleSheet()
        self._header(el, "Earning Summary Report", staff_name)
        el.append(Paragraph("Earning Summary Overview", s['h2']))
        el.append(Spacer(1, 0.2*inch))
        try:
            t = Table([[RLImage(line_path, 4.8*inch, 3.2*inch),
                        RLImage(bar_path,  4.8*inch, 3.2*inch)]],
                      colWidths=[5*inch, 5*inch])
            t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
            el.append(t)
        except Exception as e:
            el.append(Paragraph(f"Error: {e}", s['Normal']))
        doc.build(el); return fp

    def generate_rental_report(self, staff_name, rows):
        fp = f"Car_Rental_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(fp, pagesize=(11*inch, 8.5*inch))
        el = []; self._header(el, "Car Rental Report", staff_name)
        data = [["ID","Customer","Car","Date Rented","Total Price","Status"]]
        for r in rows:
            dr = r['date_rented']
            if isinstance(dr,(datetime,date)): dr = dr.strftime('%Y-%m-%d')
            data.append([str(r['rental_id']), r['customer_name'], r['car_name'],
                         dr, f"₱{float(r['total_price']):,.2f}", r['status']])
        t = Table(data, colWidths=[0.5*inch,2.5*inch,2.5*inch,1.5*inch,1.5*inch,1.2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),rl_colors.HexColor('#0f172a')),
            ('TEXTCOLOR',(0,0),(-1,0),rl_colors.white),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('BOTTOMPADDING',(0,0),(-1,0),12),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[rl_colors.white,rl_colors.HexColor('#f8fafc')]),
            ('GRID',(0,0),(-1,-1),0.5,rl_colors.HexColor('#e2e8f0')),
        ]))
        el.append(t); doc.build(el); return fp


# ── Matplotlib canvas ─────────────────────────────────────────────
class MplCanvas(FigureCanvas):
    def __init__(self, width=6, height=3.5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#ffffff')
        self.axes = self.fig.add_subplot(111, facecolor='#ffffff')
        super().__init__(self.fig)
        self.fig.tight_layout(pad=2.5)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


# ── Circular logo label ───────────────────────────────────────────
class RoundedLogoLabel(QLabel):
    def __init__(self, img_path, size=36, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size; self._pm = None
        if os.path.exists(img_path):
            src = QPixmap(img_path).scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            if src.width()!=size or src.height()!=size:
                x=(src.width()-size)//2; y=(src.height()-size)//2
                src=src.copy(x,y,size,size)
            self._pm = src
        self.setStyleSheet("background:transparent;")

    def paintEvent(self, ev):
        if not self._pm: super().paintEvent(ev); return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath(); path.addEllipse(0,0,self._size,self._size)
        p.setClipPath(path)
        p.drawPixmap(0,0,self._pm)
        p.end()


# ── StaffInterface ────────────────────────────────────────────────
class StaffInterface(QWidget):
    logout_requested = pyqtSignal()

    def __init__(self, staff_name="Staff"):
        super().__init__()
        self.staff_name  = staff_name
        self.pdf_service = PdfService()
        self.rental_data = []
        self.cars_data   = []
        self.line_data_2025 = [0]*12
        self.bar_data_2024  = [0]*12
        self.bar_data_2025  = [0]*12
        self._line_year     = 2025
        self._bar_year_a    = 2024
        self._bar_year_b    = 2025
        self.setStyleSheet(f"QWidget{{font-family:'Segoe UI',sans-serif;background:{CONTENT_BG};}}")
        self._load_all_data()
        self._build_ui()

    # ── Data ────────────────────────────────────────────────────
    def _load_all_data(self):
        self._load_rentals(); self._load_cars(); self._load_chart_data()

    def _load_rentals(self):
        rows = _db_query("""
            SELECT r.rental_id, c.customer_name, ca.car_name,
                   r.total_price, r.date_rented, r.date_returned, r.status
            FROM rentals r
            JOIN customers c ON r.customer_id=c.customer_id
            JOIN cars ca     ON r.car_id=ca.car_id
            ORDER BY r.rental_id DESC""")
        self.rental_data = rows if rows else self._fallback_rentals()

    def _load_cars(self):
        rows = _db_query("SELECT car_id, car_name, car_price FROM cars ORDER BY car_id")
        self.cars_data = rows if rows else []

    def _load_chart_data(self):
        self.line_data_2025 = self._load_year_data(self._line_year)
        self.bar_data_2024  = self._load_year_data(self._bar_year_a)
        self.bar_data_2025  = self._load_year_data(self._bar_year_b)
        if all(v==0 for v in self.line_data_2025) and self._line_year == 2025:
            self.line_data_2025=[8315,12630,16945,11265,15145,9280,13640,10410,12795,11650,14195,9400]
        if all(v==0 for v in self.bar_data_2024) and self._bar_year_a == 2024:
            self.bar_data_2024=[6060,9010,11075,13200,10075,7030,9095,7180,8045,10225,7085,6025]
        if all(v==0 for v in self.bar_data_2025) and self._bar_year_b == 2025:
            self.bar_data_2025=list(self.line_data_2025)

    def _load_year_data(self, year):
        rows = _db_query(
            "SELECT MONTH(date_rented) AS m, SUM(total_price) AS total "
            "FROM rentals WHERE YEAR(date_rented)=%s GROUP BY m ORDER BY m", (year,))
        data = [0.0] * 12
        for r in rows: data[int(r['m'])-1] = float(r['total'])
        return data

    def _fallback_rentals(self):
        return [
            {'rental_id':1,'customer_name':'Juan Dela Cruz','car_name':'Toyota Vios',
             'total_price':2005.00,'date_rented':date(2024,9,18),'date_returned':date(2024,9,22),'status':'Returned'},
            {'rental_id':2,'customer_name':'Maria Clara','car_name':'Mitsubishi Mirage',
             'total_price':2010.00,'date_rented':date(2024,2,16),'date_returned':date(2024,2,20),'status':'Pending'},
        ]

    # ── UI ──────────────────────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content())

    # ── Sidebar ────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = QFrame(); sb.setFixedWidth(220)
        sb.setStyleSheet(f"QFrame{{background:{SIDEBAR_BG};border:none;}}")
        lay = QVBoxLayout(sb); lay.setContentsMargins(0,0,0,20); lay.setSpacing(0)

        # Logo header
        logo_box = QWidget(); logo_box.setFixedHeight(70)
        logo_box.setStyleSheet(f"background:{SIDEBAR_BG};border-bottom:1px solid rgba(255,255,255,0.06);")
        ll = QHBoxLayout(logo_box); ll.setContentsMargins(16,0,16,0)

        logo = RoundedLogoLabel(LOGO_PATH, 40)
        ll.addWidget(logo); ll.addSpacing(10)

        brand_col = QVBoxLayout(); brand_col.setSpacing(1)
        b1 = QLabel("SE Enterprise")
        b1.setStyleSheet("font-size:13px;font-weight:700;color:#f1f5f9;background:transparent;")
        b2 = QLabel("Fleet Management")
        b2.setStyleSheet("font-size:10px;color:rgba(255,255,255,0.35);background:transparent;")
        brand_col.addWidget(b1); brand_col.addWidget(b2)
        ll.addLayout(brand_col); ll.addStretch()

        dot = QLabel("●")
        dot.setStyleSheet(f"font-size:7px;color:{GREEN};background:transparent;")
        ll.addWidget(dot)
        lay.addWidget(logo_box); lay.addSpacing(12)

        nav_lbl = QLabel("  MENU")
        nav_lbl.setStyleSheet("font-size:10px;color:#334155;padding:4px 20px 6px;letter-spacing:1.5px;background:transparent;font-weight:700;")
        lay.addWidget(nav_lbl)

        self.btn_dashboard = self._nav_btn("Dashboard", lay)
        self.btn_reports   = self._nav_btn("Reports",   lay)
        self.btn_cars      = self._nav_btn("Fleet",     lay)
        self.btn_dashboard.clicked.connect(lambda: self._switch(0))
        self.btn_reports.clicked.connect(lambda:   self._switch(1))
        self.btn_cars.clicked.connect(lambda:      self._switch(2))
        self.btn_dashboard.setChecked(True)
        lay.addStretch()

        # Staff card
        info_box = QFrame()
        info_box.setStyleSheet("QFrame{background:rgba(255,255,255,0.05);border-radius:10px;"
                               "border:1px solid rgba(255,255,255,0.08);margin:0 10px;}")
        ib = QHBoxLayout(info_box); ib.setContentsMargins(12,10,12,10)
        avatar = QLabel(); avatar.setFixedSize(32,32); avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"background:{GREEN};border-radius:16px;font-size:13px;"
                             "font-weight:700;color:#fff;border:none;")
        avatar.setText(self.staff_name[0].upper() if self.staff_name else "S")
        self._avatar_lbl = avatar
        ib.addWidget(avatar); ib.addSpacing(8)

        nc = QVBoxLayout(); nc.setSpacing(1)
        self._staff_label = QLabel(self.staff_name)
        self._staff_label.setStyleSheet("font-size:12px;font-weight:700;color:#e2e8f0;background:transparent;border:none;")
        rl = QLabel("Staff")
        rl.setStyleSheet("font-size:10px;color:#64748b;background:transparent;border:none;")
        nc.addWidget(self._staff_label); nc.addWidget(rl)
        ib.addLayout(nc); ib.addStretch()
        lay.addWidget(info_box); lay.addSpacing(10)

        lo = QPushButton("  Log Out")
        lo.setCursor(Qt.CursorShape.PointingHandCursor); lo.setFixedHeight(40)
        lo.setStyleSheet(
            "QPushButton{background:transparent;color:#64748b;border:1px solid rgba(255,255,255,0.08);"
            "border-radius:8px;font-size:13px;font-weight:600;margin:0 10px;}"
            "QPushButton:hover{background:rgba(239,68,68,0.12);color:#ef4444;"
            "border:1px solid rgba(239,68,68,0.3);}")
        lo.clicked.connect(self.logout_requested.emit)
        lay.addWidget(lo)
        return sb

    def _nav_btn(self, text, layout):
        btn = QPushButton(f"   {text}")
        btn.setCheckable(True); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(NAV_BTN); btn.setFixedHeight(42)
        layout.addWidget(btn); return btn

    def set_staff_name(self, name):
        self.staff_name = name
        if hasattr(self, "_staff_label"): self._staff_label.setText(name)
        if hasattr(self, "_avatar_lbl"): self._avatar_lbl.setText(name[0].upper() if name else "S")

    # ── Content ─────────────────────────────────────────────────
    def _build_content(self):
        w = QWidget(); w.setStyleSheet(f"background:{CONTENT_BG};")
        lay = QVBoxLayout(w); lay.setContentsMargins(0,0,0,0)
        self.stack = QStackedWidget(); self.stack.setStyleSheet(f"background:{CONTENT_BG};")
        self.stack.addWidget(self._build_dashboard())
        self.stack.addWidget(self._build_reports())
        self.stack.addWidget(self._build_cars_page())
        lay.addWidget(self.stack); return w

    def _switch(self, idx):
        self.stack.setCurrentIndex(idx)
        self.btn_dashboard.setChecked(idx==0)
        self.btn_reports.setChecked(idx==1)
        self.btn_cars.setChecked(idx==2)

    def _page_header(self, title, btn_text, btn_cb):
        bar = QWidget(); bar.setFixedHeight(68)
        bar.setStyleSheet(f"background:#fff;border-bottom:1px solid {BORDER};")
        lay = QHBoxLayout(bar); lay.setContentsMargins(28,0,28,0)
        t = QLabel(title)
        t.setStyleSheet(f"font-size:20px;font-weight:800;color:{TEXT_PRIMARY};"
                        "letter-spacing:-0.5px;background:transparent;")
        lay.addWidget(t); lay.addStretch()
        btn = QPushButton(btn_text); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(38); btn.setStyleSheet(EXPORT_BTN)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(12); sh.setOffset(QPointF(0,3)); sh.setColor(QColor(34,197,94,60))
        btn.setGraphicsEffect(sh)
        btn.clicked.connect(btn_cb)
        lay.addWidget(btn); return bar, btn

    # ── KPI card — NO border-left hack, use inner accent bar instead ──
    def _kpi_card(self, label, value, subtitle, color):
        card = QFrame(); card.setMinimumHeight(108)
        card.setStyleSheet(
            f"QFrame{{background:{CARD_BG};border-radius:14px;border:1px solid {BORDER};}}")
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(14); sh.setOffset(QPointF(0,3)); sh.setColor(QColor(0,0,0,12))
        card.setGraphicsEffect(sh)

        root = QVBoxLayout(card); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Coloured top stripe — 4px tall, clean
        stripe = QWidget(); stripe.setFixedHeight(4)
        stripe.setStyleSheet(f"background:{color};border-radius:14px 14px 0 0;border:none;")
        root.addWidget(stripe)

        inner = QHBoxLayout(); inner.setContentsMargins(20,14,20,16)
        text_col = QVBoxLayout(); text_col.setSpacing(3)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size:11px;font-weight:700;color:{TEXT_MUTED};"
                          "background:transparent;letter-spacing:0.4px;text-transform:uppercase;")
        val = QLabel(value)
        val.setStyleSheet(f"font-size:26px;font-weight:800;color:{TEXT_PRIMARY};"
                          "background:transparent;letter-spacing:-0.5px;")
        sub = QLabel(subtitle)
        sub.setStyleSheet(f"font-size:11px;color:{TEXT_MUTED};background:transparent;")
        text_col.addWidget(lbl); text_col.addWidget(val); text_col.addWidget(sub)
        inner.addLayout(text_col); inner.addStretch()
        root.addLayout(inner)
        return card

    def _tab_btn(self, text):
        btn = QPushButton(text); btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.setFixedHeight(36)
        btn.setStyleSheet(f"""
QPushButton {{
    background: #fff; color: {TEXT_MUTED};
    border: 1.5px solid {BORDER}; border-radius: 9px;
    font-size: 13px; font-weight: 600; padding: 0 18px;
}}
QPushButton:checked {{ background: {GREEN}; color: #fff; border-color: {GREEN}; }}
QPushButton:hover:!checked {{ background: #f0fdf4; border-color: {GREEN}; color:{GREEN}; }}
"""); return btn

    # ── DASHBOARD ────────────────────────────────────────────────
    def _build_dashboard(self):
        outer = QWidget(); outer.setStyleSheet(f"background:{CONTENT_BG};")
        lay = QVBoxLayout(outer); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        hdr, self._dash_export_btn = self._page_header(
            "Dashboard", "Export Earnings PDF", self._export_current_dashboard)
        lay.addWidget(hdr)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea{{background:{CONTENT_BG};border:none;}}{SCROLLBAR}")
        page = QWidget(); page.setStyleSheet(f"background:{CONTENT_BG};")
        pl = QVBoxLayout(page); pl.setContentsMargins(28,22,28,28); pl.setSpacing(20)

        total = len(self.rental_data)
        rev   = sum(float(r['total_price']) for r in self.rental_data)
        ret   = sum(1 for r in self.rental_data if r['status']=='Returned')
        pend  = sum(1 for r in self.rental_data if r['status']=='Pending')

        kpi_row = QHBoxLayout(); kpi_row.setSpacing(14)
        kpi_row.addWidget(self._kpi_card("Total Revenue", f"₱{rev:,.0f}", "All time earnings", GREEN))
        kpi_row.addWidget(self._kpi_card("Total Rentals", str(total),      "Transactions",      "#3b82f6"))
        kpi_row.addWidget(self._kpi_card("Returned",      str(ret),        "Completed",         GREEN))
        kpi_row.addWidget(self._kpi_card("Pending",       str(pend),       "Awaiting return",   "#f59e0b"))
        pl.addLayout(kpi_row)

        tab_row = QHBoxLayout(); tab_row.setSpacing(8)
        self.dash_tab_earn = self._tab_btn("Earning Summary")
        self.dash_tab_rent = self._tab_btn("Car Rentals")
        tab_row.addWidget(self.dash_tab_earn); tab_row.addWidget(self.dash_tab_rent)
        tab_row.addStretch(); pl.addLayout(tab_row)

        self.dash_stack = QStackedWidget()
        self.dash_stack.setStyleSheet(f"background:{CONTENT_BG};")
        self.dash_stack.addWidget(self._build_earning_panel())
        self.dash_stack.addWidget(self._build_rental_panel())
        pl.addWidget(self.dash_stack)

        self.dash_tab_earn.clicked.connect(lambda: self._dash_switch(0))
        self.dash_tab_rent.clicked.connect(lambda: self._dash_switch(1))
        self._dash_switch(0)
        scroll.setWidget(page); lay.addWidget(scroll)
        return outer

    def _dash_switch(self, idx):
        self.dash_stack.setCurrentIndex(idx)
        self.dash_tab_earn.setChecked(idx==0)
        self.dash_tab_rent.setChecked(idx==1)
        lbl = "Export Earnings PDF" if idx==0 else "Export Rental PDF"
        if hasattr(self,"_dash_export_btn"): self._dash_export_btn.setText(lbl)

    def _export_current_dashboard(self):
        if self.dash_stack.currentIndex()==0: self._export_earnings_pdf()
        else: self._export_rental_pdf()

    def _build_earning_panel(self):
        panel = QWidget(); panel.setStyleSheet(f"background:{CONTENT_BG};")
        lay = QVBoxLayout(panel); lay.setContentsMargins(0,8,0,0); lay.setSpacing(14)
        self.canvas_line = MplCanvas(); self.canvas_bar = MplCanvas()
        self._draw_line_chart(); self._draw_bar_chart()
        self.canvas_line.mpl_connect('button_press_event', lambda e: self._open_line_zoom())
        self.canvas_bar.mpl_connect('button_press_event',  lambda e: self._open_bar_zoom())

        cr = QHBoxLayout(); cr.setSpacing(16)

        # ── Line chart wrap ──
        line_wrap = QFrame()
        line_wrap.setStyleSheet(f"QFrame{{background:{CARD_BG};border-radius:14px;border:1px solid {BORDER};}}")
        sh1 = QGraphicsDropShadowEffect()
        sh1.setBlurRadius(14); sh1.setOffset(QPointF(0,3)); sh1.setColor(QColor(0,0,0,10))
        line_wrap.setGraphicsEffect(sh1)
        wl1 = QVBoxLayout(line_wrap); wl1.setContentsMargins(18,14,18,14)
        line_hdr = QHBoxLayout()
        self._line_cap = QLabel(f"Monthly Earnings — {self._line_year}")
        self._line_cap.setStyleSheet(f"font-size:13px;font-weight:700;color:{TEXT_PRIMARY};background:transparent;")
        self._line_cap.setCursor(Qt.CursorShape.PointingHandCursor)
        self._line_cap.mousePressEvent = lambda e: self._pick_line_year()
        line_hdr.addWidget(self._line_cap)
        cur_year = datetime.now().year
        if self._line_year == cur_year:
            self._ongoing_badge = QLabel("Ongoing")
            self._ongoing_badge.setStyleSheet(f"background:{GREEN_BG};color:{GREEN_DARK};border:1px solid {GREEN_BORDER};"
                                              "border-radius:6px;padding:2px 8px;font-size:10px;font-weight:700;")
            line_hdr.addWidget(self._ongoing_badge)
        line_hdr.addStretch()
        tip1 = QLabel("Click title to change year  ·  Click chart to expand")
        tip1.setStyleSheet(f"font-size:10px;color:{TEXT_MUTED};background:transparent;")
        line_hdr.addWidget(tip1)
        wl1.addLayout(line_hdr); wl1.addSpacing(4); wl1.addWidget(self.canvas_line)
        cr.addWidget(line_wrap)

        # ── Bar chart wrap ──
        bar_wrap = QFrame()
        bar_wrap.setStyleSheet(f"QFrame{{background:{CARD_BG};border-radius:14px;border:1px solid {BORDER};}}")
        sh2 = QGraphicsDropShadowEffect()
        sh2.setBlurRadius(14); sh2.setOffset(QPointF(0,3)); sh2.setColor(QColor(0,0,0,10))
        bar_wrap.setGraphicsEffect(sh2)
        wl2 = QVBoxLayout(bar_wrap); wl2.setContentsMargins(18,14,18,14)
        bar_hdr = QHBoxLayout()
        self._bar_cap = QLabel(f"Year Comparison — {self._bar_year_a} vs {self._bar_year_b}")
        self._bar_cap.setStyleSheet(f"font-size:13px;font-weight:700;color:{TEXT_PRIMARY};background:transparent;")
        self._bar_cap.setCursor(Qt.CursorShape.PointingHandCursor)
        self._bar_cap.mousePressEvent = lambda e: self._pick_bar_years()
        bar_hdr.addWidget(self._bar_cap); bar_hdr.addStretch()
        tip2 = QLabel("Click title to change years  ·  Click chart to expand")
        tip2.setStyleSheet(f"font-size:10px;color:{TEXT_MUTED};background:transparent;")
        bar_hdr.addWidget(tip2)
        wl2.addLayout(bar_hdr); wl2.addSpacing(4); wl2.addWidget(self.canvas_bar)
        cr.addWidget(bar_wrap)

        lay.addLayout(cr); return panel

    def _pick_line_year(self):
        cur_year = datetime.now().year
        years = [str(y) for y in range(2023, cur_year + 1)]
        dlg = QDialog(self); dlg.setWindowTitle("Select Year"); dlg.setFixedWidth(260)
        dlg.setStyleSheet("background:#fff;")
        lay = QVBoxLayout(dlg); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)
        lbl = QLabel("Select year for Monthly Earnings:")
        lbl.setStyleSheet(f"font-size:13px;font-weight:600;color:{TEXT_PRIMARY};background:transparent;")
        lay.addWidget(lbl)
        btn_grid = QVBoxLayout(); btn_grid.setSpacing(6)
        for y in reversed(years):
            btn = QPushButton(y); btn.setFixedHeight(38)
            is_cur = int(y) == cur_year
            is_sel = int(y) == self._line_year
            if is_sel:
                btn.setStyleSheet(f"QPushButton{{background:{GREEN};color:#fff;border-radius:8px;font-weight:700;font-size:13px;border:none;}}")
            else:
                btn.setStyleSheet(f"QPushButton{{background:#f8fafc;color:{TEXT_PRIMARY};border-radius:8px;font-weight:600;font-size:13px;border:1px solid {BORDER};}}QPushButton:hover{{background:#f0fdf4;color:{GREEN};border-color:{GREEN};}}")
            label_text = f"{y}  (Ongoing)" if is_cur else y
            btn.setText(label_text)
            btn.clicked.connect(lambda _, yr=int(y): self._set_line_year(yr, dlg))
            btn_grid.addWidget(btn)
        lay.addLayout(btn_grid); dlg.exec()

    def _set_line_year(self, year, dlg):
        self._line_year = year
        self.line_data_2025 = self._load_year_data(year)
        self._draw_line_chart()
        self._line_cap.setText(f"Monthly Earnings — {year}")
        cur_year = datetime.now().year
        if hasattr(self, '_ongoing_badge'):
            self._ongoing_badge.setVisible(year == cur_year)
        dlg.accept()

    def _pick_bar_years(self):
        cur_year = datetime.now().year
        years = list(range(2023, cur_year + 1))
        dlg = QDialog(self); dlg.setWindowTitle("Compare Years"); dlg.setFixedWidth(300)
        dlg.setStyleSheet("background:#fff;")
        lay = QVBoxLayout(dlg); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)
        lbl = QLabel("Select two years to compare:")
        lbl.setStyleSheet(f"font-size:13px;font-weight:600;color:{TEXT_PRIMARY};background:transparent;")
        lay.addWidget(lbl)

        from PyQt6.QtWidgets import QComboBox as QCB
        row1 = QHBoxLayout()
        l1 = QLabel("Year A:"); l1.setStyleSheet(f"font-size:12px;color:{TEXT_MUTED};background:transparent;min-width:52px;")
        cb1 = QCB(); cb1.setFixedHeight(38)
        cb1.setStyleSheet(f"background:#f8fafc;border:1.5px solid {BORDER};border-radius:8px;padding:6px 12px;font-size:13px;color:{TEXT_PRIMARY};")
        for y in reversed(years): cb1.addItem(str(y))
        cb1.setCurrentText(str(self._bar_year_a))
        row1.addWidget(l1); row1.addWidget(cb1); lay.addLayout(row1)

        row2 = QHBoxLayout()
        l2 = QLabel("Year B:"); l2.setStyleSheet(f"font-size:12px;color:{TEXT_MUTED};background:transparent;min-width:52px;")
        cb2 = QCB(); cb2.setFixedHeight(38)
        cb2.setStyleSheet(f"background:#f8fafc;border:1.5px solid {BORDER};border-radius:8px;padding:6px 12px;font-size:13px;color:{TEXT_PRIMARY};")
        for y in reversed(years): cb2.addItem(str(y) + ("  (Ongoing)" if y == cur_year else ""))
        cb2.setCurrentText(str(self._bar_year_b) + ("  (Ongoing)" if self._bar_year_b == cur_year else ""))
        row2.addWidget(l2); row2.addWidget(cb2); lay.addLayout(row2)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        cancel = QPushButton("Cancel"); cancel.setFixedHeight(38)
        cancel.setStyleSheet(f"QPushButton{{background:#f1f5f9;color:{TEXT_PRIMARY};border-radius:8px;font-weight:600;font-size:13px;border:1px solid {BORDER};}}QPushButton:hover{{background:#e2e8f0;}}")
        apply = QPushButton("Apply"); apply.setFixedHeight(38)
        apply.setStyleSheet(f"QPushButton{{background:{GREEN};color:#fff;border-radius:8px;font-weight:700;font-size:13px;border:none;}}QPushButton:hover{{background:{GREEN_DARK};}}")
        btn_row.addWidget(cancel); btn_row.addWidget(apply); lay.addLayout(btn_row)
        cancel.clicked.connect(dlg.reject)
        def do_apply():
            ya = int(cb1.currentText())
            yb_text = cb2.currentText().split()[0]
            yb = int(yb_text)
            self._bar_year_a = ya; self._bar_year_b = yb
            self.bar_data_2024 = self._load_year_data(ya)
            self.bar_data_2025 = self._load_year_data(yb)
            self._draw_bar_chart()
            self._bar_cap.setText(f"Year Comparison — {ya} vs {yb}")
            dlg.accept()
        apply.clicked.connect(do_apply)
        dlg.exec()

    def _build_rental_panel(self):
        panel = QWidget(); panel.setStyleSheet(f"background:{CONTENT_BG};")
        lay = QVBoxLayout(panel); lay.setContentsMargins(0,8,0,0); lay.setSpacing(10)
        sr = QHBoxLayout()
        self._dash_search = QLineEdit(); self._dash_search.setPlaceholderText("Search rentals...")
        self._dash_search.setFixedWidth(300); self._dash_search.setFixedHeight(40)
        self._dash_search.setStyleSheet(SEARCH_INPUT)
        self._dash_search.textChanged.connect(self._search_dash_table)
        sr.addWidget(self._dash_search); sr.addStretch(); lay.addLayout(sr)

        wrap = QFrame()
        wrap.setStyleSheet(f"QFrame{{background:{CARD_BG};border-radius:14px;border:1px solid {BORDER};}}")
        wl = QVBoxLayout(wrap); wl.setContentsMargins(0,0,0,0)
        self._dash_rental_table = self._make_table(["ID","Customer","Car","Date Rented","Total Price","Status"])
        wl.addWidget(self._dash_rental_table); lay.addWidget(wrap)
        self._filter_dash_table('all'); return panel

    def _filter_dash_table(self, status):
        data = self.rental_data if status=='all' else [r for r in self.rental_data if r['status']==status]
        self._dash_rental_table.setRowCount(len(data))
        for i,r in enumerate(data): self._fill_rental_row(self._dash_rental_table, i, r)
        self._dash_rental_table.verticalHeader().setDefaultSectionSize(52)

    def _search_dash_table(self, text):
        for row in range(self._dash_rental_table.rowCount()):
            match = any(text.lower() in (self._dash_rental_table.item(row,col).text().lower()
                        if self._dash_rental_table.item(row,col) else '')
                        for col in range(self._dash_rental_table.columnCount()-1))
            self._dash_rental_table.setRowHidden(row, not match)

    # ── REPORTS ─────────────────────────────────────────────────
    def _build_reports(self):
        outer = QWidget(); outer.setStyleSheet(f"background:{CONTENT_BG};")
        lay = QVBoxLayout(outer); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        hdr, _ = self._page_header("Reports","Export Rental PDF",self._export_rental_pdf)
        lay.addWidget(hdr)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea{{background:{CONTENT_BG};border:none;}}{SCROLLBAR}")
        page = QWidget(); page.setStyleSheet(f"background:{CONTENT_BG};")
        pl = QVBoxLayout(page); pl.setContentsMargins(28,22,28,28); pl.setSpacing(20)

        total = len(self.rental_data)
        ret   = sum(1 for r in self.rental_data if r['status']=='Returned')
        pend  = sum(1 for r in self.rental_data if r['status']=='Pending')
        rev   = sum(float(r['total_price']) for r in self.rental_data)

        cards = QHBoxLayout(); cards.setSpacing(14)
        for lbl, val, color, cb in [
            ("Total Rentals", str(total),     "#3b82f6", lambda e: self._populate_reports_table('all')),
            ("Returned",      str(ret),       GREEN,     lambda e: self._populate_reports_table('Returned')),
            ("Pending",       str(pend),      "#f59e0b", lambda e: self._populate_reports_table('Pending')),
            ("Total Revenue", f"₱{rev:,.0f}", GREEN,     lambda e: self.show_revenue_details()),
        ]:
            c = self._kpi_card(lbl, val, "Click to filter", color)
            c.setCursor(Qt.CursorShape.PointingHandCursor); c.mousePressEvent = cb
            cards.addWidget(c)
        pl.addLayout(cards)

        wrap = QFrame()
        wrap.setStyleSheet(f"QFrame{{background:{CARD_BG};border-radius:14px;border:1px solid {BORDER};}}")
        wl = QVBoxLayout(wrap); wl.setContentsMargins(0,0,0,0)
        self.reports_table = self._make_table(["ID","Customer","Car","Date Rented","Total Price","Status"])
        wl.addWidget(self.reports_table); pl.addWidget(wrap)
        self._populate_reports_table('all')
        scroll.setWidget(page); lay.addWidget(scroll); return outer

    def show_revenue_details(self):
        returned=[r for r in self.rental_data if r['status']=='Returned']
        pending =[r for r in self.rental_data if r['status']=='Pending']
        rv=sum(float(r['total_price']) for r in returned)
        pv=sum(float(r['total_price']) for r in pending)
        QMessageBox.information(self,"Revenue Details",
            f"Returned ({len(returned)}): ₱{rv:,.2f}\nPending ({len(pending)}): ₱{pv:,.2f}\n\nTotal: ₱{rv+pv:,.2f}")

    def _populate_reports_table(self, status):
        data = self.rental_data if status=='all' else [r for r in self.rental_data if r['status']==status]
        self.reports_table.setRowCount(len(data))
        for i,r in enumerate(data): self._fill_rental_row(self.reports_table, i, r)
        self.reports_table.verticalHeader().setDefaultSectionSize(52)

    # ── FLEET PAGE ──────────────────────────────────────────────
    def _build_cars_page(self):
        outer = QWidget(); outer.setStyleSheet(f"background:{CONTENT_BG};")
        lay = QVBoxLayout(outer); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # Header bar
        hdr_bar = QWidget(); hdr_bar.setFixedHeight(68)
        hdr_bar.setStyleSheet(f"background:#fff;border-bottom:1px solid {BORDER};")
        hl = QHBoxLayout(hdr_bar); hl.setContentsMargins(28,0,28,0)
        t = QLabel("Fleet")
        t.setStyleSheet(f"font-size:20px;font-weight:800;color:{TEXT_PRIMARY};background:transparent;")
        hl.addWidget(t); hl.addStretch()
        sb = QLineEdit(); sb.setPlaceholderText("Search vehicles...")
        sb.setFixedWidth(260); sb.setFixedHeight(38); sb.setStyleSheet(SEARCH_INPUT)
        sb.textChanged.connect(self._filter_cars_cards)
        hl.addWidget(sb)
        lay.addWidget(hdr_bar)

        # Body: grid left + add-car panel right
        body = QWidget(); body.setStyleSheet(f"background:{CONTENT_BG};")
        body_lay = QHBoxLayout(body); body_lay.setContentsMargins(0,0,0,0); body_lay.setSpacing(0)

        # Left: scrollable car grid
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea{{background:{CONTENT_BG};border:none;}}{SCROLLBAR}")
        page = QWidget(); page.setStyleSheet(f"background:{CONTENT_BG};")
        pg = QVBoxLayout(page); pg.setContentsMargins(28,22,14,28); pg.setSpacing(0)

        cnt_row = QHBoxLayout()
        self._fleet_count = QLabel(f"{len(self.cars_data)} vehicles in fleet")
        self._fleet_count.setStyleSheet(f"font-size:13px;color:{TEXT_MUTED};font-weight:500;background:transparent;")
        cnt_row.addWidget(self._fleet_count); cnt_row.addStretch()
        pg.addLayout(cnt_row); pg.addSpacing(14)

        self._cars_grid_wrap = QWidget(); self._cars_grid_wrap.setStyleSheet("background:transparent;")
        self._cars_grid = QGridLayout(self._cars_grid_wrap)
        self._cars_grid.setSpacing(14); self._cars_grid.setContentsMargins(0,0,0,0)
        pg.addWidget(self._cars_grid_wrap); pg.addStretch()
        self._render_car_cards("")
        scroll.setWidget(page)
        body_lay.addWidget(scroll, stretch=1)

        # Right: Add Car panel
        body_lay.addWidget(self._build_add_car_panel())
        lay.addWidget(body, stretch=1)
        return outer

    def _build_add_car_panel(self):
        panel = QFrame()
        panel.setFixedWidth(280)
        panel.setStyleSheet(
            f"QFrame{{background:#fff;border-left:1px solid {BORDER};border-radius:0px;}}")

        lay = QVBoxLayout(panel); lay.setContentsMargins(20,24,20,24); lay.setSpacing(14)

        # Title
        title = QLabel("Add New Vehicle")
        title.setStyleSheet(f"font-size:15px;font-weight:800;color:{TEXT_PRIMARY};"
                            "background:transparent;letter-spacing:-0.3px;")
        lay.addWidget(title)

        sub = QLabel("Fill in the details and upload a photo")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"font-size:11px;color:{TEXT_MUTED};background:transparent;")
        lay.addWidget(sub)

        # Divider
        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color:{BORDER};"); lay.addWidget(div)

        # Photo picker
        photo_lbl = QLabel("VEHICLE PHOTO")
        photo_lbl.setStyleSheet(f"font-size:10px;font-weight:700;color:{TEXT_MUTED};"
                                "background:transparent;letter-spacing:1px;")
        lay.addWidget(photo_lbl)

        self._photo_preview = QLabel()
        self._photo_preview.setFixedHeight(130)
        self._photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._photo_preview.setStyleSheet(
            f"background:#f8fafc;border-radius:10px;border:2px dashed #cbd5e1;"
            "color:#94a3b8;font-size:12px;")
        self._photo_preview.setText("Click to select photo")
        self._photo_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self._photo_preview.mousePressEvent = lambda e: self._pick_photo()
        lay.addWidget(self._photo_preview)
        self._selected_photo_path = None

        change_btn = QPushButton("Browse Photo")
        change_btn.setFixedHeight(34)
        change_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_btn.setStyleSheet(
            f"QPushButton{{background:#f1f5f9;color:{TEXT_PRIMARY};border-radius:7px;"
            f"font-weight:600;font-size:12px;border:1px solid {BORDER};}}"
            f"QPushButton:hover{{background:#e2e8f0;}}")
        change_btn.clicked.connect(self._pick_photo)
        lay.addWidget(change_btn)

        # Car name
        nl = QLabel("CAR NAME")
        nl.setStyleSheet(f"font-size:10px;font-weight:700;color:{TEXT_MUTED};"
                         "background:transparent;letter-spacing:1px;")
        lay.addWidget(nl)
        self._add_name_input = QLineEdit()
        self._add_name_input.setObjectName("addInp")
        self._add_name_input.setPlaceholderText("e.g. Toyota Corolla")
        self._add_name_input.setFixedHeight(42)
        self._add_name_input.setStyleSheet(ADD_INPUT)
        lay.addWidget(self._add_name_input)

        # Price
        pl2 = QLabel("PRICE PER DAY (₱)")
        pl2.setStyleSheet(f"font-size:10px;font-weight:700;color:{TEXT_MUTED};"
                          "background:transparent;letter-spacing:1px;")
        lay.addWidget(pl2)
        self._add_price_input = QLineEdit()
        self._add_price_input.setPlaceholderText("e.g. 350")
        self._add_price_input.setFixedHeight(42)
        self._add_price_input.setStyleSheet(ADD_INPUT)
        lay.addWidget(self._add_price_input)

        lay.addStretch()

        # Add button
        add_btn = QPushButton("Add Vehicle to Fleet")
        add_btn.setFixedHeight(46)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            f"QPushButton{{background:{GREEN};color:#fff;border:none;"
            f"border-radius:10px;font-size:14px;font-weight:700;}}"
            f"QPushButton:hover{{background:{GREEN_DARK};}}"
            f"QPushButton:pressed{{background:#15803d;}}")
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(14); sh.setOffset(QPointF(0,4)); sh.setColor(QColor(34,197,94,60))
        add_btn.setGraphicsEffect(sh)
        add_btn.clicked.connect(self._add_car)
        lay.addWidget(add_btn)
        return panel

    def _pick_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Vehicle Photo", "",
            "Images (*.jpg *.jpeg *.png *.bmp *.webp)")
        if path:
            self._selected_photo_path = path
            px = QPixmap(path).scaled(
                240, 126,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            self._photo_preview.setPixmap(px)
            self._photo_preview.setStyleSheet(
                "background:#f0fdf4;border-radius:10px;border:2px solid #bbf7d0;")

    def _add_car(self):
        name  = self._add_name_input.text().strip()
        price = self._add_price_input.text().strip()

        if not name:
            QMessageBox.warning(self,"Missing Name","Please enter a car name."); return
        try:
            price_val = float(price)
        except ValueError:
            QMessageBox.warning(self,"Invalid Price","Please enter a valid price."); return

        # Insert into DB
        new_id = _db_exec(
            "INSERT INTO cars (car_name, car_price) VALUES (%s, %s)",
            (name, price_val))

        if new_id is None:
            QMessageBox.critical(self,"DB Error","Could not insert car into database."); return

        # Copy photo to resources directory
        if self._selected_photo_path:
            ext = os.path.splitext(self._selected_photo_path)[1]
            dest = os.path.join(RES_DIR, f"{name}.jpg")
            try:
                # Convert and save as JPEG for consistency
                from PyQt6.QtGui import QImage as QImg
                img = QImg(self._selected_photo_path)
                img.save(dest, "JPEG", 90)
            except Exception:
                try: shutil.copy2(self._selected_photo_path, dest)
                except Exception as e:
                    print(f"Photo copy failed: {e}")

        # Reset form
        self._add_name_input.clear()
        self._add_price_input.clear()
        self._selected_photo_path = None
        self._photo_preview.setPixmap(QPixmap())
        self._photo_preview.setText("Click to select photo")
        self._photo_preview.setStyleSheet(
            "background:#f8fafc;border-radius:10px;border:2px dashed #cbd5e1;"
            "color:#94a3b8;font-size:12px;")

        # Reload cars and refresh grid
        self._load_cars()
        self._render_car_cards("")
        QMessageBox.information(self,"Added",
            f"'{name}' has been added to the fleet (ID: {new_id}).")

    # ── Shared Helpers ───────────────────────────────────────────
    def _make_table(self, headers):
        t = QTableWidget(); t.setColumnCount(len(headers)); t.setHorizontalHeaderLabels(headers)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.setAlternatingRowColors(True); t.setShowGrid(False)
        t.verticalHeader().setVisible(False); t.setFrameShape(QFrame.Shape.NoFrame)
        t.setStyleSheet(TABLE_STYLE + SCROLLBAR)
        hdr = t.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in range(t.columnCount()):
            if i!=1: hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        if len(headers)==6 and 'Status' in headers:
            hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
            t.setColumnWidth(5, 130)
        return t

    def _ci(self, text):
        it = QTableWidgetItem(str(text))
        it.setTextAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignVCenter)
        return it

    def _fill_rental_row(self, table, idx, r):
        table.setItem(idx,0,self._ci(r['rental_id']))
        table.setItem(idx,1,QTableWidgetItem(f"  {r['customer_name']}"))
        table.setItem(idx,2,QTableWidgetItem(f"  {r['car_name']}"))
        dr = r['date_rented']
        if isinstance(dr,(datetime,date)): dr=dr.strftime('%Y-%m-%d')
        table.setItem(idx,3,self._ci(dr))
        pi = QTableWidgetItem(f"₱{float(r['total_price']):,.2f}")
        pi.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        table.setItem(idx,4,pi)
        status=r['status']
        container=QWidget(); container.setStyleSheet("background:transparent;")
        hlay=QHBoxLayout(container); hlay.setContentsMargins(8,4,8,4)
        hlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pill=QLabel(status); pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pill.setMinimumWidth(84); pill.setMinimumHeight(26)
        pill.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        base="border-radius:13px;font-weight:700;font-size:11px;padding:4px 14px;"
        if status=='Returned':
            pill.setStyleSheet(base+f"background:{GREEN_BG};color:{GREEN_DARK};border:1.5px solid {GREEN_BORDER};")
        elif status=='Pending':
            pill.setStyleSheet(base+f"background:{RED_BG};color:{RED};border:1.5px solid {RED_BORDER};")
        else:
            pill.setStyleSheet(base+"background:#f1f5f9;color:#475569;border:1.5px solid #cbd5e1;")
        hlay.addWidget(pill); table.setCellWidget(idx,5,container)

    def _render_car_cards(self, text):
        while self._cars_grid.count():
            item=self._cars_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        filtered=[c for c in self.cars_data if text.lower() in str(c['car_name']).lower()]
        cols=4
        for i,car in enumerate(filtered):
            self._cars_grid.addWidget(self._car_card(car), i//cols, i%cols)
        self._cars_grid.setColumnStretch(cols,1)
        if hasattr(self,'_fleet_count'):
            self._fleet_count.setText(f"{len(filtered)} vehicle{'s' if len(filtered)!=1 else ''} in fleet")

    def _filter_cars_cards(self, text): self._render_car_cards(text)

    def _car_card(self, car):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame{{background:{CARD_BG};border-radius:14px;border:1.5px solid {BORDER};}}"
            f"QFrame:hover{{border-color:{GREEN};background:#f0fdf4;}}")
        card.setFixedSize(210, 200)
        sh=QGraphicsDropShadowEffect()
        sh.setBlurRadius(10); sh.setOffset(QPointF(0,2)); sh.setColor(QColor(0,0,0,9))
        card.setGraphicsEffect(sh)
        lay=QVBoxLayout(card); lay.setContentsMargins(12,12,12,12); lay.setSpacing(3)

        # Top row: ID badge + Edit/Delete buttons
        top_row=QHBoxLayout(); top_row.setSpacing(4)
        id_b=QLabel(f"#{car['car_id']}")
        id_b.setFixedHeight(20)
        id_b.setStyleSheet(f"background:{GREEN_BG};color:{GREEN_DARK};font-size:10px;font-weight:700;"
                           "border-radius:4px;padding:1px 7px;border:none;")
        id_b.setMaximumWidth(38)
        top_row.addWidget(id_b); top_row.addStretch()

        edit_btn=QPushButton("Edit"); edit_btn.setFixedSize(38,20)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setStyleSheet(
            f"QPushButton{{background:#eff6ff;color:#3b82f6;border:1px solid #bfdbfe;"
            "border-radius:4px;font-size:9px;font-weight:700;padding:0;}}"
            "QPushButton:hover{background:#dbeafe;}")
        edit_btn.clicked.connect(lambda _, c=car: self._edit_car(c))

        del_btn=QPushButton("Del"); del_btn.setFixedSize(30,20)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(
            f"QPushButton{{background:{RED_BG};color:{RED};border:1px solid {RED_BORDER};"
            "border-radius:4px;font-size:9px;font-weight:700;padding:0;}}"
            f"QPushButton:hover{{background:#fecaca;}}")
        del_btn.clicked.connect(lambda _, c=car: self._delete_car(c))

        top_row.addWidget(edit_btn); top_row.addWidget(del_btn)
        lay.addLayout(top_row)

        name=QLabel(str(car['car_name']))
        name.setStyleSheet(f"color:{TEXT_PRIMARY};font-size:13px;font-weight:700;background:transparent;")
        name.setWordWrap(True)
        price=QLabel(f"₱{float(car.get('car_price') or 0):,.0f} / day")
        price.setStyleSheet(f"color:{TEXT_MUTED};font-size:11px;font-weight:600;background:transparent;")

        img=QLabel(); img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img.setFixedHeight(98); img.setStyleSheet("background:transparent;")
        ip=os.path.join(BASE_DIR,"..","resources",f"{car['car_name']}.jpg")
        if os.path.exists(ip):
            px=QPixmap(ip).scaled(164,92,Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            img.setPixmap(px)

        lay.addWidget(name); lay.addWidget(price)
        lay.addStretch(); lay.addWidget(img); lay.addStretch()
        return card

    def _edit_car(self, car):
        dlg = QDialog(self); dlg.setWindowTitle("Edit Vehicle"); dlg.setFixedWidth(340)
        dlg.setStyleSheet("background:#fff;")
        lay = QVBoxLayout(dlg); lay.setContentsMargins(24,24,24,24); lay.setSpacing(12)

        title = QLabel("Edit Vehicle")
        title.setStyleSheet(f"font-size:15px;font-weight:800;color:{TEXT_PRIMARY};background:transparent;")
        lay.addWidget(title)

        id_lbl = QLabel("CAR ID")
        id_lbl.setStyleSheet(f"font-size:10px;font-weight:700;color:{TEXT_MUTED};background:transparent;letter-spacing:1px;")
        lay.addWidget(id_lbl)
        id_inp = QLineEdit(str(car['car_id'])); id_inp.setFixedHeight(42)
        id_inp.setReadOnly(True)
        id_inp.setStyleSheet(f"background:#f1f5f9;border:1.5px solid {BORDER};border-radius:8px;padding:10px 13px;font-size:13px;color:{TEXT_MUTED};")
        lay.addWidget(id_inp)

        name_lbl = QLabel("CAR NAME")
        name_lbl.setStyleSheet(f"font-size:10px;font-weight:700;color:{TEXT_MUTED};background:transparent;letter-spacing:1px;")
        lay.addWidget(name_lbl)
        name_inp = QLineEdit(car['car_name']); name_inp.setFixedHeight(42); name_inp.setStyleSheet(ADD_INPUT)
        lay.addWidget(name_inp)

        price_lbl = QLabel("PRICE PER DAY (₱)")
        price_lbl.setStyleSheet(f"font-size:10px;font-weight:700;color:{TEXT_MUTED};background:transparent;letter-spacing:1px;")
        lay.addWidget(price_lbl)
        price_inp = QLineEdit(str(car['car_price'])); price_inp.setFixedHeight(42); price_inp.setStyleSheet(ADD_INPUT)
        lay.addWidget(price_inp)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        cancel = QPushButton("Cancel"); cancel.setFixedHeight(40)
        cancel.setStyleSheet(f"QPushButton{{background:#f1f5f9;color:{TEXT_PRIMARY};border-radius:8px;font-weight:600;font-size:13px;border:1px solid {BORDER};}}QPushButton:hover{{background:#e2e8f0;}}")
        save = QPushButton("Save Changes"); save.setFixedHeight(40)
        save.setStyleSheet(f"QPushButton{{background:{GREEN};color:#fff;border-radius:8px;font-weight:700;font-size:13px;border:none;}}QPushButton:hover{{background:{GREEN_DARK};}}")
        btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

        cancel.clicked.connect(dlg.reject)
        def do_save():
            new_name = name_inp.text().strip()
            try: new_price = float(price_inp.text().strip())
            except ValueError: QMessageBox.warning(dlg, "Invalid", "Enter a valid price."); return
            if not new_name: QMessageBox.warning(dlg, "Invalid", "Enter a car name."); return
            _db_exec("UPDATE cars SET car_name=%s, car_price=%s WHERE car_id=%s",
                     (new_name, new_price, car['car_id']))
            self._load_cars(); self._render_car_cards(""); dlg.accept()
        save.clicked.connect(do_save)
        dlg.exec()

    def _delete_car(self, car):
        reply = QMessageBox.question(self, "Delete Vehicle",
            f"Are you sure you want to delete '{car['car_name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            _db_exec("DELETE FROM cars WHERE car_id=%s", (car['car_id'],))
            self._load_cars(); self._render_car_cards("")

    # ── Charts ──────────────────────────────────────────────────
    def _style_ax(self,ax):
        ax.set_facecolor('#ffffff'); ax.figure.set_facecolor('#ffffff')
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.yaxis.grid(True,color='#f1f5f9',linestyle='--',linewidth=0.8)
        ax.xaxis.grid(False); ax.set_axisbelow(True)
        ax.tick_params(colors='#94a3b8',labelsize=9,length=0)

    def _draw_line_chart(self):
        self._plot_line(self.canvas_line.axes, self.line_data_2025, self._line_year)
        self.canvas_line.figure.canvas.draw_idle()

    def _draw_bar_chart(self):
        self._plot_bar(self.canvas_bar.axes, self.bar_data_2024, self.bar_data_2025, self._bar_year_a, self._bar_year_b)
        self.canvas_bar.figure.canvas.draw_idle()

    def _plot_line(self, ax, data, year=2025):
        ax.clear()
        months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        cur_month = datetime.now().month if year == datetime.now().year else 12
        x = range(12)
        ax.fill_between(x, data, alpha=0.12, color='#22c55e')
        ax.plot(x, data, marker='o', color='#22c55e', linewidth=2.5, markersize=6,
                markerfacecolor='white', markeredgecolor='#22c55e', markeredgewidth=2.5)
        if year == datetime.now().year and cur_month < 12:
            ax.axvline(x=cur_month-1, color='#f59e0b', linewidth=1.2, linestyle='--', alpha=0.7)
            ax.text(cur_month-0.7, ax.get_ylim()[1]*0.95 if max(data)>0 else 100,
                    'Ongoing', color='#f59e0b', fontsize=8, fontweight='bold')
        ax.set_xticks(range(12)); ax.set_xticklabels(months, fontsize=9)
        self._style_ax(ax)
        mx = max(data)
        if mx > 0:
            mi = list(data).index(mx)
            ax.annotate(f'₱{mx:,.0f}', xy=(mi,mx), xytext=(0,12), textcoords='offset points',
                        ha='center', color='#16a34a', fontsize=8, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#dcfce7', edgecolor='none'))

    def _plot_bar(self, ax, d_a, d_b, year_a=2024, year_b=2025):
        ax.clear()
        months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        x=np.arange(12); w=0.4
        ax.bar(x-w/2, d_a, width=w, color='#e2e8f0', edgecolor='none', label=str(year_a), zorder=2)
        ax.bar(x+w/2, d_b, width=w, color='#22c55e', edgecolor='none',
               label=f"{year_b} (Ongoing)" if year_b == datetime.now().year else str(year_b), zorder=2)
        ax.set_xticks(x); ax.set_xticklabels(months, fontsize=9)
        ax.legend(fontsize=9, framealpha=0, labelcolor='#64748b', loc='upper right')
        self._style_ax(ax)

    def _open_line_zoom(self):
        dlg=QDialog(self); dlg.setWindowTitle(f"Monthly Earnings {self._line_year}")
        dlg.resize(960,540); dlg.setStyleSheet("background:#fff;")
        lay=QVBoxLayout(dlg); lay.setContentsMargins(20,20,20,20)
        c=MplCanvas(width=9,height=4.5,dpi=100)
        self._plot_line(c.axes, self.line_data_2025, self._line_year); c.figure.canvas.draw_idle()
        lay.addWidget(c); dlg.exec()

    def _open_bar_zoom(self):
        dlg=QDialog(self); dlg.setWindowTitle(f"Earnings Comparison {self._bar_year_a} vs {self._bar_year_b}")
        dlg.resize(960,540); dlg.setStyleSheet("background:#fff;")
        lay=QVBoxLayout(dlg); lay.setContentsMargins(20,20,20,20)
        c=MplCanvas(width=9,height=4.5,dpi=100)
        self._plot_bar(c.axes, self.bar_data_2024, self.bar_data_2025, self._bar_year_a, self._bar_year_b); c.figure.canvas.draw_idle()
        lay.addWidget(c); dlg.exec()

    # ── PDF ─────────────────────────────────────────────────────
    def _export_earnings_pdf(self):
        try:
            tmp=tempfile.gettempdir()
            lp=os.path.join(tmp,'line.png'); bp=os.path.join(tmp,'bar.png')
            self.canvas_line.fig.savefig(lp,dpi=150,bbox_inches='tight',facecolor='#fff')
            self.canvas_bar.fig.savefig(bp,dpi=150,bbox_inches='tight',facecolor='#fff')
            out=self.pdf_service.generate_earnings_report(self.staff_name,lp,bp)
            for p in (lp,bp):
                if os.path.exists(p): os.remove(p)
            QMessageBox.information(self,"Saved",f"Earnings PDF saved:\n{out}")
        except Exception as e:
            QMessageBox.critical(self,"Export Failed",str(e))

    def _export_rental_pdf(self):
        try:
            out=self.pdf_service.generate_rental_report(self.staff_name,self.rental_data)
            QMessageBox.information(self,"Saved",f"Rental PDF saved:\n{out}")
        except Exception as e:
            QMessageBox.critical(self,"Export Failed",str(e))


if __name__=="__main__":
    app=QApplication(sys.argv); app.setStyle("Fusion")
    win=QMainWindow(); win.setWindowTitle("Staff Dashboard"); win.resize(1300,800)
    ui=StaffInterface(staff_name="Demo Staff"); win.setCentralWidget(ui); win.show()
    sys.exit(app.exec())