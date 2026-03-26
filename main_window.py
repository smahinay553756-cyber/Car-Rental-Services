import sys
from datetime import date
from PyQt6.QtWidgets import QWidget, QStackedWidget, QApplication, QVBoxLayout
from .login_interface import LoginInterface
from .staff_interface import StaffInterface
from .customer_interface import CustomerInterface
from .my_rental_page import MyRentalPage
from .customer_type_dialog import CustomerTypeDialog


def _auto_return_overdue():
    """Mark any Pending rentals whose due date has passed as Returned."""
    try:
        import pymysql
        from datetime import timedelta
        cfg = {"host": "localhost", "user": "root", "password": "",
               "database": "se_enterprise",
               "cursorclass": pymysql.cursors.DictCursor, "connect_timeout": 5}
        today = date.today()
        with pymysql.connect(**cfg) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT r.rental_id, r.date_rented, r.total_price, ca.car_price
                    FROM rentals r
                    JOIN cars ca ON r.car_id = ca.car_id
                    WHERE r.status = 'Pending' AND r.date_rented IS NOT NULL
                """)
                rows = cur.fetchall() or []
                overdue_ids = []
                for r in rows:
                    try:
                        days = round(float(r['total_price']) / float(r['car_price']))
                        days = max(1, days)
                    except Exception:
                        days = 1
                    due_date = r['date_rented'] + timedelta(days=days)
                    if today > due_date:
                        overdue_ids.append(r['rental_id'])
                if overdue_ids:
                    fmt = ','.join(['%s'] * len(overdue_ids))
                    cur.execute(
                        f"UPDATE rentals SET status='Returned', date_returned=%s "
                        f"WHERE rental_id IN ({fmt})",
                        [today] + overdue_ids)
                    conn.commit()
    except Exception as e:
        print(f"[auto-return] {e}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Car Rental System")
        self.resize(1200, 800)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        self.login_page    = LoginInterface()
        self.staff_page    = StaffInterface()
        self.customer_page = CustomerInterface()
        self.my_rental_page = MyRentalPage()

        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.staff_page)
        self.stacked_widget.addWidget(self.customer_page)
        self.stacked_widget.addWidget(self.my_rental_page)

        self.login_page.login_successful.connect(self.route_login)
        self.staff_page.logout_requested.connect(self.show_login_page)
        self.customer_page.logout_requested.connect(self.show_login_page)
        self.customer_page.rental_confirmed.connect(self._show_my_rental)
        self.my_rental_page.back_requested.connect(self._back_to_customer)
        self.my_rental_page.logout_requested.connect(self.show_login_page)
        self.my_rental_page.rent_again.connect(self._on_rent_again)
        self.my_rental_page.rent_another.connect(self._on_rent_another)

        self.center_window()
        _auto_return_overdue()

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def route_login(self, user_type, username):
        if user_type == 'staff':
            self.staff_page.set_staff_name(username)
            self.stacked_widget.setCurrentWidget(self.staff_page)
        elif user_type == 'customer':
            self._show_customer_type_dialog()

    def _show_customer_type_dialog(self):
        dlg = CustomerTypeDialog(self)
        dlg.new_customer.connect(self._on_new_customer)
        dlg.returning_customer.connect(self._on_returning_customer)
        dlg.exec()

    def _on_new_customer(self):
        self.customer_page.load_cars()
        # Clear any previous prefill
        for attr in ('name_input', 'contact_input', 'street_input', 'barangay_input', 'city_input'):
            getattr(self.customer_page, attr).clear()
        self.customer_page.selected_car = None
        self.customer_page.selected_car_label.setText("No vehicle selected")
        self.customer_page.total_price_input.clear()
        self.stacked_widget.setCurrentWidget(self.customer_page)

    def _on_returning_customer(self, customer: dict, rentals: list):
        self.my_rental_page.load_returning(customer, rentals)
        self.stacked_widget.setCurrentWidget(self.my_rental_page)

    def _show_my_rental(self, info):
        self.my_rental_page.load_rental(info)
        self.stacked_widget.setCurrentWidget(self.my_rental_page)

    def _back_to_customer(self):
        _auto_return_overdue()
        self.customer_page.load_cars()
        self.stacked_widget.setCurrentWidget(self.customer_page)

    def _on_rent_again(self, customer: dict, car: dict):
        _auto_return_overdue()
        self.customer_page.load_cars()
        self.customer_page.prefill(customer, car)
        self.stacked_widget.setCurrentWidget(self.customer_page)

    def _on_rent_another(self, customer: dict):
        _auto_return_overdue()
        self.customer_page.load_cars()
        self.customer_page.prefill(customer, None)
        self.stacked_widget.setCurrentWidget(self.customer_page)

    def show_login_page(self):
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.login_page.password_input.clear()
