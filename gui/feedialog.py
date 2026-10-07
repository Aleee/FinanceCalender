import html
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

import lovely_logger as log

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDialog, QFileDialog

from base.date import date_str, date_displstr
from base.dbhandler import DBHandler
from base.feeparser import CSVParseError, DailyFees, FeeCategoryResult, StatementParseResult, read_transaction_csv
from base.formatting import dec_strcommaspace, dec_html, COLOR_HEADER_BG, COLOR_WARNING, COLOR_WARNING_BG
from base.liability import LiabilityCategory, FilterFlags, RowType, calculate_filterflags
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
        self.ui.chb_fullreport.clicked.connect(self.show_report)

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
            self.parse_result = read_transaction_csv(file_path, self.dbh)
        except (CSVParseError, OSError, UnicodeDecodeError) as exc:
            self.parse_result = None
            log.w(f"Не удалось прочитать CSV-файл с комиссиями: {exc}")
            ErrorInfoMessageBox(f"Не удалось прочитать CSV-файл: {exc}").exec()
            return

        self.show_report()

    def show_report(self) -> None:
        result = self.parse_result
        if result is None:
            return
        period_from = result.period[0].strftime("%d.%m.%Y")
        period_to = result.period[1].strftime("%d.%m.%Y")

        render_category = self._render_category_full if self.ui.chb_fullreport.isChecked() \
            else self._render_category_report
        text = f"<h3>Выписка за период {period_from} – {period_to}</h3>"
        text += render_category("Комиссии банка, удержанные из поступлений", result.income_fees)
        text += render_category("Комиссии, уплаченные/списанные отдельно", result.outgoing_fees)

        has_any_fees = bool(result.income_fees.daily or result.outgoing_fees.daily)
        self.ui.pb_createfeeliabilities.setEnabled(has_any_fees)
        self.ui.te_info.setHtml(text)

    @staticmethod
    def _render_category_report(title: str, fees: FeeCategoryResult) -> str:
        if not fees.daily:
            return (f"<h4>{title}</h4><p>Транзакций с комиссией не обнаружено.</p>"
                    + FeeDialog._render_suspicious(fees, full=False))

        total_count = sum(agg.count for agg in fees.daily.values())
        total_sum = sum(agg.total for agg in fees.daily.values())

        lines = [
            f"<h4>{title}</h4>",
            "<table cellspacing='0' cellpadding='4'>",
            f"<tr bgcolor='{COLOR_HEADER_BG}'><th align='left'>Дата</th>"
            f"<th align='right'>Транзакций</th><th align='right'>Сумма комиссий</th></tr>",
        ]
        for fee_date, agg in fees.daily.items():
            lines.append(
                f"<tr><td>{fee_date.strftime('%d.%m.%Y')}</td>"
                f"<td align='right'>{agg.count}</td><td align='right'>{dec_html(agg.total)}</td></tr>"
            )
        lines.append(
            f"<tr bgcolor='{COLOR_HEADER_BG}'><td><b>Итого</b></td>"
            f"<td align='right'><b>{total_count}</b></td><td align='right'><b>{dec_html(total_sum)}</b></td></tr>"
        )
        lines.append("</table>")

        if fees.unknown_unp:
            lines.append(FeeDialog._render_unknown_unp_warning(len(fees.unknown_unp), in_table=False))
            lines.append("<table cellspacing='0' cellpadding='3'>")
            for unp, unp_date, name in fees.unknown_unp:
                lines.append(
                    f"<tr><td>{html.escape(unp)}</td><td>{html.escape(name)}</td>"
                    f"<td>{unp_date.strftime('%d.%m.%Y')}</td></tr>"
                )
            lines.append("</table>")

        lines.append(FeeDialog._render_suspicious(fees, full=False))

        return "\n".join(lines)

    @staticmethod
    def _render_category_full(title: str, fees: FeeCategoryResult) -> str:
        if not fees.records:
            return (f"<h4>{title}</h4><p>Транзакций с комиссией не обнаружено.</p>"
                    + FeeDialog._render_suspicious(fees, full=True))

        total_sum = sum(record.amount for record in fees.records)
        lines = [
            f"<h4>{title}</h4>",
            f"<p>Всего комиссий: {len(fees.records)} на сумму {dec_html(total_sum)}</p>",
        ]
        if fees.unknown_unp:
            lines.append(FeeDialog._render_unknown_unp_warning(len(fees.unknown_unp), in_table=True))

        lines.append("<table width='100%' cellspacing='0' cellpadding='4' border='1' "
                     "style='border-collapse:collapse; border-color:#c8c8c8;'>")
        lines.append(
            f"<tr bgcolor='{COLOR_HEADER_BG}'><th>№</th><th>Сумма</th>"
            f"<th>Контрагент</th><th>Назначение платежа</th></tr>"
        )
        current_date = None
        for number, record in enumerate(sorted(fees.records, key=lambda r: r.fee_date), start=1):
            if record.fee_date != current_date:
                current_date = record.fee_date
                lines.append(
                    f"<tr bgcolor='{COLOR_HEADER_BG}'><td colspan='4' align='center'><b>{current_date.strftime('%d.%m.%Y')}</b></td></tr>"
                )
            row_bg = "" if record.is_known_unp else f" bgcolor='{COLOR_WARNING_BG}'"
            lines.append(
                f"<tr{row_bg}><td align='right' valign='top'>{number}</td>"
                f"<td align='right' valign='top'>{dec_html(record.amount)}</td>"
                f"<td valign='top'>{html.escape(record.receiver)}</td>"
                f"<td valign='top'>{html.escape(' '.join(record.description.split()))}</td></tr>"
            )
        lines.append("</table>")
        lines.append(FeeDialog._render_suspicious(fees, full=True))
        return "\n".join(lines)

    @staticmethod
    def _render_unknown_unp_warning(count: int, in_table: bool) -> str:
        where = "Такие строки выделены в таблице цветом." if in_table else "Список записей приведён ниже."
        return (
            f"<p style='color:{COLOR_WARNING}; background-color:{COLOR_WARNING_BG};'>"
            f"<b>Внимание!</b> Среди транзакций замечены записи с УНП, которых нет в списке УНП банков "
            f"(всего {count}). Проверьте эти записи на правильность включения в список уплаченных комиссий! "
            f"При необходимости добавьте эти УНП в список УНП банков в настройках. {where}</p>"
        )

    @staticmethod
    def _render_suspicious(fees: FeeCategoryResult, full: bool) -> str:
        if not fees.suspicious:
            return ""

        lines = [
            f"<p style='color:{COLOR_WARNING}; background-color:{COLOR_WARNING_BG};'>"
            f"<b>Внимание!</b> Обнаружены подозрительные операции с кодом 6 (всего {len(fees.suspicious)}): "
            f"выполняется только одно из условий — УНП банка или ключевые слова. "
            f"В комиссии такие операции НЕ включены. Проверьте их вручную; "
            f"при необходимости скорректируйте список УНП банков или ключевые слова в настройках.</p>",
            "<table cellspacing='0' cellpadding='3'>",
        ]
        for item in sorted(fees.suspicious, key=lambda s: s.record.fee_date):
            record = item.record
            description_cell = f"<td>{html.escape(' '.join(record.description.split()))}</td>" if full else ""
            lines.append(
                f"<tr><td>{record.fee_date.strftime('%d.%m.%Y')}</td>"
                f"<td>{html.escape(record.unp)}</td><td>{html.escape(record.receiver)}</td>"
                f"<td align='right'>{dec_html(record.amount)}</td>"
                f"<td>{html.escape(item.reason)}</td>{description_cell}</tr>"
            )
        lines.append("</table>")
        return "\n".join(lines)

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

        created_count = 0
        for daily, liability_category, description in categories:
            for fee_date, agg in daily.items():
                if not self._create_fee_liability(fee_date, agg, liability_category, description):
                    if created_count:
                        ErrorInfoMessageBox(
                            f"До момента ошибки было успешно создано {created_count} записей о комиссиях. "
                            f"Проверьте список обязательств, чтобы не создать дубликаты при повторном запуске."
                        ).exec()
                    return False
                created_count += 1

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
            text += f"- {date_label} ({liability_category.name}) на сумму {dec_strcommaspace(amount, add_rub=True)}\n"
        text += "Возможны, будут созданы дублирующие записи. Уверены, что хотите продолжить?"
        return YesNoMessagebox(text).exec() != YesNoMessagebox.NO_RETURN_VALUE

    def _create_fee_liability(
        self, fee_date: date, agg: DailyFees, category: LiabilityCategory, description: str
    ) -> bool:
        qt_fee_date = QDate(fee_date.year, fee_date.month, fee_date.day)
        fee_date_str = date_str(qt_fee_date)
        today_str = date_str(QDate.currentDate())
        comment = agg.as_comment()

        filter_flags: FilterFlags = calculate_filterflags(
            Decimal("0.0"), qt_fee_date, False, QDate.currentDate()
        )

        event_data: list = [
            FEE_RECEIVER,
            0,
            int(RowType.LIABILITY),
            0,
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
            self.dbh.get_setting("CSVparser/responsible", "0"),
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
            log.e(f"Не удалось вставить новую строку в таблицу event со следующими данными: {event_data}")
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
            log.e(f"Не удалось вставить новую строку в таблицу payment со следующими данными: {payment_data}")
            return False

        return True