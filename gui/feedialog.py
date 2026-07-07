from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Optional
import lovely_logger as log

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDialog, QFileDialog

from base.date import date_str
from base.dbhandler import DBHandler
from base.feesparser import read_transaction_csv
from base.formatting import dec_strcommaspace, str_rubstr
from base.liability import LiabilityCategory, FilterFlags, RowType
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.eventsqlmodel import LiabilitySqlTableModel, Col
from gui.paymenthistorymodel import PaymentHistoryTableModel
from gui.paymenthistoryproxymodel import PaymentHistoryProxyModel
from gui.settings import SettingsHandler
from gui.ui.feedialog_ui import Ui_feedialog


FEE_RECEIVER: str = "Банки"


class FeeDialog(QDialog):
    def __init__(self, settings_handler, db_handler, base_model, payment_model, parent=None):
        super(FeeDialog, self).__init__(parent)
        self.ui = Ui_feedialog()
        self.ui.setupUi(self)

        self.sh: SettingsHandler = settings_handler
        self.dbh: DBHandler = db_handler
        self.base_model: LiabilitySqlTableModel = base_model
        self.payment_model: PaymentHistoryTableModel = payment_model

        self.startdate: Optional[date] = None
        self.enddate: Optional[date] = None
        self.results: Optional[dict] = None
        self.unknown_unp: Optional[list] = None
        self.notes_info: Optional[dict] = None

        self.ui.pb_opencsv.clicked.connect(self.open_csv)
        self.ui.pb_createfeeliabilities.clicked.connect(self.make_fee_payments)

    def open_csv(self) -> None:
        file_path: str = QFileDialog.getOpenFileName(parent=self, caption="Выберите выписку",
                                                     dir=self.sh.settings.value("CSVparser/lastloadpath") if
                                                     self.sh.settings.value("CSVparser/lastloadpath") and Path(self.sh.settings.value("CSVparser/lastloadpath")).is_dir()
                                                     else "",
                                                     filter="Файл выписки в формате CSV (*.csv)")[0]
        if not file_path:
            return
        self.sh.settings.setValue("CSVparser/lastloadpath", str(Path(file_path).parent))
        self.ui.te_info.clear()
        self.ui.pb_createfeeliabilities.setEnabled(False)
        result = read_transaction_csv(file_path, self.sh)
        if not result:
            ErrorInfoMessageBox("Не удалось прочитать CSV-файл (см. подробности в логе)").exec()
        else:
            self.results = result[0]
            self.startdate = result[1][0]
            self.enddate = result[1][1]
            self.unknown_unp = result[2]
            self.notes_info = result[3]
            self.show_report()

    def show_report(self) -> None:
        text = f"Загружена выписка с <b>{self.startdate.strftime("%d.%m.%Y")}</b> по <b>{self.enddate.strftime("%d.%m.%Y")}</b><br>"
        if self.results:
            text += f"Всего транзакций с уплаченной комиссией: <b>{sum(value[0] for value in self.results.values())}</b><br><i>в том числе:</i><br>"
            for key, value in self.results.items():
                text += f"- {key.strftime("%d.%m.%Y")}: транзакций - {value[0]}, сумма комиссий - {str(value[1])} руб.<br>"
            text += f"Всего уплачено комиссий за период - <b>{sum(value[1] for value in self.results.values())} руб.</b><br>"
            if self.unknown_unp:
                text += (f"Внимание! Среди транзакций замечены записи с неизвестными УНП плательщика (всего {len(self.unknown_unp)}). Проверьте эти записи "
                         f"на правильность включения в список уплаченных комиссий! При необходимости добавьте эти УНП в список доверенных в настройках.<br>")
            for value in self.unknown_unp:
                text += f"- <b>{value[0]}</b>: {value[2]} ({value[1].strftime("%d.%m.%Y")})<br>"
            self.ui.pb_createfeeliabilities.setEnabled(True)
        else:
            text += "Транзакций с уплаченной комиссией не обнаружено."
        self.ui.pb_createfeeliabilities.setEnabled(bool(self.results))
        self.ui.te_info.setText(text)

    def make_fee_payments(self) -> bool:
        already_paid: list = []
        for fee_date in self.results.keys():
            check_result = self.dbh.check_fees_paid_fordate(QDate(fee_date.year, fee_date.month, fee_date.day))
            if check_result is None:
                ErrorInfoMessageBox("Не удалось выполнить запрос к базе данных (см. подробности в логе)").exec()
                return False
            elif check_result.is_nan():
                continue
            else:
                already_paid.append((fee_date, check_result))

        if already_paid:
            text = "В базе данных обнаружены уже имеющиеся записи об оплаченных комиссиях за следующие даты:\n"
            for entry in already_paid:
                text += f"- {entry[0].strftime("%d.%m.%Y")} на сумму {entry[1]} руб.\n"
            text += "Возможны, будут созданы дублирующие записи. Уверены, что хотите продолжить?"
            if YesNoMessagebox(text).exec() == YesNoMessagebox.NO_RETURN_VALUE:
                return False

        for fee_date, fee_values in self.results.items():
            data: list = list()
            qt_fee_date = QDate(fee_date.year, fee_date.month, fee_date.day)
            data.append(FEE_RECEIVER)
            data.append(0)
            data.append(int(RowType.LIABILITY))
            data.append(int(LiabilityCategory.COMMISSION))
            data.append(0)
            data.append(f"[A] Комиссионное вознаграждение банку")
            data.append(str(Decimal("0.0")))
            data.append(str(fee_values[1]))
            data.append(0)
            data.append(date_str(qt_fee_date))
            data.append(date_str(QDate.currentDate()))
            data.append(1)
            data.append(f"Автоматический учет комиссий за {fee_date.strftime("%d.%m.%Y")} (транзакций: {fee_values[0]})")
            data.append(self.sh.settings.value("CSVparser/responsible", "0"))
            note = ""
            if self.notes_info is not None:
                for entry in self.notes_info[fee_date]:
                    note += f"{entry[0]}: {str_rubstr(dec_strcommaspace(entry[1]))}\n"
            data.append(note)
            data.append(str(Decimal("0.0")))
            data.append(date_str(qt_fee_date))
            filter_flags: FilterFlags = self.base_model.calculate_filterflags(Decimal("0.0"), qt_fee_date, False, QDate.currentDate())
            data.append(int(filter_flags))
            data.append(0)
            data.append(0)
            data.append(str.lower(FEE_RECEIVER))
            new_event_row = self.base_model.insert_row(data)
            if not new_event_row:
                ErrorInfoMessageBox("При создании записи об уплаченной комиссии произошла ошибка (подробнее см. лог)")
                log.c(f"Не удалось вставить новую строку в таблицу event со следующими данными: {data}")
                return False

            self.base_model.submitAll()

            data = list()
            data.append(self.base_model.index(new_event_row, Col.ID).data(LiabilitySqlTableModel.qtValueRole))
            data.append(date_str(qt_fee_date))
            data.append(str(fee_values[1]))
            data.append(date_str(QDate.currentDate()))
            if not self.payment_model.append_row(data):
                ErrorInfoMessageBox("При создании записи об уплаченной комиссии произошла ошибка (подробнее см. лог)")
                log.c(f"Не удалось вставить новую строку в таблицу payment со следующими данными: {data}")
                return False

        ErrorInfoMessageBox("Операция завершена успешно", is_info=True).exec()
        return True
