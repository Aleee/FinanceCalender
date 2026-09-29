from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

import lovely_logger as log

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDialog, QFileDialog

from base.date import date_str, date_displstr
from base.dbhandler import DBHandler
from base.feeparser import CSVParseError, DailyFees, StatementParseResult, read_transaction_csv
from base.liability import LiabilityCategory, FilterFlags, RowType
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.eventsqlmodel import LiabilitySqlTableModel, Col
from gui.paymenthistorymodel import PaymentHistoryTableModel
from gui.settings import SettingsHandler
from gui.ui.feedialog_ui import Ui_feedialog


FEE_RECEIVER: str = "Банки"

# Соответствие между категорией из парсера, категорией начисления в базе
# и текстом описания платежа. Порядок задаёт порядок создания платежей на дату.
BANKING_DESCRIPTION: str = "[A] Комиссия банка, удержанная из поступлений"
COMMISSION_DESCRIPTION: str = "[A] Комиссионное вознаграждение банку"


class FeeDialog(QDialog):
    def __init__(self, settings_handler, db_handler, base_model, payment_model, parent=None):
        super(FeeDialog, self).__init__(parent)
        self.ui = Ui_feedialog()
        self.ui.setupUi(self)

        self.sh: SettingsHandler = settings_handler
        self.dbh: DBHandler = db_handler
        self.base_model: LiabilitySqlTableModel = base_model
        self.payment_model: PaymentHistoryTableModel = payment_model

        self.parse_result: Optional[StatementParseResult] = None

        self.ui.pb_opencsv.clicked.connect(self.open_csv)
        self.ui.pb_createfeeliabilities.clicked.connect(self.make_fee_payments)

    # ------------------------------------------------------------------ #
    # Загрузка и отображение выписки
    # ------------------------------------------------------------------ #

    def open_csv(self) -> None:
        last_path = self.sh.settings.value("CSVparser/lastloadpath")
        file_path: str = QFileDialog.getOpenFileName(
            parent=self,
            caption="Выберите выписку",
            dir=last_path if last_path and Path(last_path).is_dir() else "",
            filter="Файл выписки в формате CSV (*.csv)",)[0]
        if not file_path:
            return

        self.sh.settings.setValue("CSVparser/lastloadpath", str(Path(file_path).parent))
        self.ui.te_info.clear()
        self.ui.pb_createfeeliabilities.setEnabled(False)

        try:
            self.parse_result = read_transaction_csv(file_path, self.sh)
        except CSVParseError as exc:
            self.parse_result = None
            ErrorInfoMessageBox(f"Не удалось прочитать CSV-файл: {exc}").exec()
            return

        self.show_report()

    def show_report(self) -> None:
        result = self.parse_result
        period_from = result.period[0].strftime("%d.%m.%Y")
        period_to = result.period[1].strftime("%d.%m.%Y")

        text = f"Загружена выписка с <b>{period_from}</b> по <b>{period_to}</b><br>"
        text += self._render_category_report("Комиссии банка, удержанные из поступлений", result.income_fees.daily,
                                               result.income_fees.unknown_unp)
        text += self._render_category_report("Комиссии, уплаченные/списанные отдельно", result.outgoing_fees.daily,
                                               result.outgoing_fees.unknown_unp)

        has_any_fees = bool(result.income_fees.daily or result.outgoing_fees.daily)
        self.ui.pb_createfeeliabilities.setEnabled(has_any_fees)
        self.ui.te_info.setText(text)

    @staticmethod
    def _render_category_report(title: str, daily: dict[date, DailyFees], unknown_unp: list) -> str:
        if not daily:
            return f"<b>{title}:</b> транзакций не обнаружено.<br>"

        total_count = sum(agg.count for agg in daily.values())
        total_sum = sum(agg.total for agg in daily.values())

        text = f"<b>{title}:</b> всего транзакций с комиссией — <b>{total_count}</b><br><i>в том числе:</i><br>"
        for fee_date, agg in daily.items():
            date_label = fee_date.strftime("%d.%m.%Y")
            text += f"- {date_label}: транзакций - {agg.count}, сумма комиссий - {agg.total} руб.<br>"
        text += f"Итого за период — <b>{total_sum} руб.</b><br>"

        if unknown_unp:
            text += (
                f"Внимание! Среди транзакций замечены записи с неизвестными УНП плательщика "
                f"(всего {len(unknown_unp)}). Проверьте эти записи на правильность включения "
                f"в список уплаченных комиссий! При необходимости добавьте эти УНП в список доверенных "
                f"в настройках.<br>"
            )
            for unp, unp_date, name in unknown_unp:
                text += f"- <b>{unp}</b>: {name} ({unp_date.strftime('%d.%m.%Y')})<br>"

        return text

    # ------------------------------------------------------------------ #
    # Создание платежей
    # ------------------------------------------------------------------ #

    def make_fee_payments(self) -> bool:
        if self.parse_result is None:
            return False

        # (данные категории из парсера, категория начисления в базе, текст описания платежа)
        categories = [
            (self.parse_result.income_fees.daily, LiabilityCategory.BANKING, BANKING_DESCRIPTION),
            (self.parse_result.outgoing_fees.daily, LiabilityCategory.COMMISSION, COMMISSION_DESCRIPTION),
        ]

        already_paid = self._check_already_paid(categories)
        if already_paid is None:
            return False  # ошибка запроса к БД, сообщение уже показано
        if already_paid and not self._confirm_duplicate_payments(already_paid):
            return False

        for daily, liability_category, description in categories:
            for fee_date, agg in daily.items():
                if not self._create_fee_liability(fee_date, agg, liability_category, description):
                    return False

        ErrorInfoMessageBox("Операция завершена успешно", is_info=True).exec()
        self.close()
        return True

    def _check_already_paid(self, categories: list) -> Optional[list]:
        """Возвращает список (дата, категория, уже сохранённая сумма) или None при ошибке БД."""
        already_paid: list = []
        for daily, liability_category, _ in categories:
            for fee_date in daily:
                check_result = self.dbh.check_fees_paid_fordate(
                    QDate(fee_date.year, fee_date.month, fee_date.day), int(liability_category)
                )
                if check_result is None:
                    ErrorInfoMessageBox("Не удалось выполнить запрос к базе данных (см. подробности в логе)").exec()
                    return None
                if not check_result.is_nan():
                    already_paid.append((fee_date, liability_category, check_result))
        return already_paid

    @staticmethod
    def _confirm_duplicate_payments(already_paid: list) -> bool:
        text = "В базе данных обнаружены уже имеющиеся записи об оплаченных комиссиях за следующие даты:\n"
        for fee_date, liability_category, amount in already_paid:
            date_label = fee_date.strftime("%d.%m.%Y")
            text += f"- {date_label} ({liability_category.name}) на сумму {amount} руб.\n"
        text += "Возможны, будут созданы дублирующие записи. Уверены, что хотите продолжить?"
        return YesNoMessagebox(text).exec() != YesNoMessagebox.NO_RETURN_VALUE

    def _create_fee_liability(
        self, fee_date: date, agg: DailyFees, category: LiabilityCategory, description: str
    ) -> bool:
        qt_fee_date = QDate(fee_date.year, fee_date.month, fee_date.day)
        fee_date_str = date_str(qt_fee_date)
        today_str = date_str(QDate.currentDate())
        comment = agg.as_comment()

        filter_flags: FilterFlags = self.base_model.calculate_filterflags(
            Decimal("0.0"), qt_fee_date, False, QDate.currentDate()
        )

        event_data: list = [
            FEE_RECEIVER,
            0,
            int(RowType.LIABILITY),
            int(category),
            0,
            description,
            str(Decimal("0.0")),
            str(agg.total),
            0,
            fee_date_str,
            today_str,
            1,
            f"Выписка от {date_displstr(qt_fee_date)}",
            self.sh.settings.value("CSVparser/responsible", "0"),
            comment,
            str(Decimal("0.0")),
            fee_date_str,
            int(filter_flags),
            0,
            0,
            str.lower(FEE_RECEIVER),
        ]

        new_event_row = self.base_model.insert_row(event_data)
        if not new_event_row:
            ErrorInfoMessageBox("При создании записи об уплаченной комиссии произошла ошибка (подробнее см. лог)").exec()
            log.c(f"Не удалось вставить новую строку в таблицу event со следующими данными: {event_data}")
            return False
        self.base_model.submitAll()

        payment_data: list = [
            self.base_model.index(new_event_row, Col.ID).data(LiabilitySqlTableModel.qtValueRole),
            fee_date_str,
            str(agg.total),
            today_str,
        ]
        if not self.payment_model.append_row(payment_data):
            ErrorInfoMessageBox("При создании записи об уплаченной комиссии произошла ошибка (подробнее см. лог)").exec()
            log.c(f"Не удалось вставить новую строку в таблицу payment со следующими данными: {payment_data}")
            return False

        return True