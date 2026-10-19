import html
import json
import os

from PySide6.QtCore import QPoint, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import (QAbstractTextDocumentLayout, QColor, QFont, QIcon, QImage, QImageReader, QKeySequence, QPalette, QShortcut, QTextCharFormat,
                           QTextCursor, QTextDocument)
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QSplitter,
                               QStackedWidget, QStyle, QStyledItemDelegate, QStyleOptionViewItem, QTextBrowser, QTextEdit,
                               QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from base.edition import is_viewer
from base.paths import manual_dir
from gui.settings import SettingsHandler


def normalize_text(text: str) -> str:
    return text.lower().replace("ё", "е")


def match_offsets(text: str, query: str) -> list[int]:
    haystack: str = normalize_text(text)
    offsets: list[int] = []
    start: int = haystack.find(query)
    while start != -1:
        offsets.append(start)
        start = haystack.find(query, start + len(query))
    return offsets


def read_blocks(document: QTextDocument) -> list[tuple[int, str]]:
    blocks: list[tuple[int, str]] = []
    block = document.begin()
    while block.isValid():
        if block.text().strip():
            blocks.append((block.position(), block.text()))
        block = block.next()
    return blocks


class SearchResultDelegate(QStyledItemDelegate):
    HTML_ROLE = Qt.ItemDataRole.UserRole + 1
    PADDING = 6

    def make_document(self, option: QStyleOptionViewItem, index) -> QTextDocument:
        document = QTextDocument()
        document.setDefaultFont(option.font)
        document.setHtml(index.data(self.HTML_ROLE))
        document.setTextWidth(option.widget.viewport().width() - 2 * self.PADDING)
        return document

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        document = self.make_document(option, index)
        return QSize(int(document.idealWidth()), int(document.size().height()) + 2 * self.PADDING)

    def paint(self, painter, option: QStyleOptionViewItem, index) -> None:
        option = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        option.text = ""
        option.widget.style().drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)
        context = QAbstractTextDocumentLayout.PaintContext()
        is_selected: bool = bool(option.state & QStyle.StateFlag.State_Selected)
        context.palette.setColor(QPalette.ColorRole.Text, option.palette.highlightedText().color() if is_selected
                                 else option.palette.text().color())
        painter.save()
        painter.translate(option.rect.topLeft() + QPoint(self.PADDING, self.PADDING))
        document = self.make_document(option, index)
        document.documentLayout().draw(painter, context)
        painter.restore()
        painter.setPen(QColor("#d8dde5"))
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())


class ManualBrowser(QTextBrowser):
    IMAGE_RESCALE_DELAY_MS = 250
    PAGE_FONT_SIZE = 10.5

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.document().setDocumentMargin(18)
        page_font: QFont = self.document().defaultFont()
        page_font.setPointSizeF(self.PAGE_FONT_SIZE)
        self.document().setDefaultFont(page_font)
        palette: QPalette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#222222"))
        for role in (QPalette.ColorRole.Highlight, QPalette.ColorRole.HighlightedText):
            palette.setColor(QPalette.ColorGroup.Inactive, role, palette.color(QPalette.ColorGroup.Active, role))
        self.setPalette(palette)
        self.image_width_limit: int = 0
        self.rescale_timer = QTimer(self)
        self.rescale_timer.setSingleShot(True)
        self.rescale_timer.setInterval(self.IMAGE_RESCALE_DELAY_MS)
        self.rescale_timer.timeout.connect(self.rescale_images)

    def available_image_width(self) -> int:
        return max(200, self.viewport().width() - 2 * int(self.document().documentMargin()) - 4)

    def loadResource(self, resource_type: int, name: QUrl):
        if resource_type == QTextDocument.ResourceType.ImageResource.value and name.isLocalFile():
            image: QImage = self.load_image(name.toLocalFile())
            if not image.isNull():
                return image
        return super().loadResource(resource_type, name)

    def load_image(self, path: str) -> QImage:
        reader = QImageReader(path)
        size: QSize = reader.size()
        ratio: float = self.devicePixelRatioF()
        self.image_width_limit = self.available_image_width()
        target: QSize = size
        if size.width() > self.image_width_limit:
            target = QSize(self.image_width_limit, round(size.height() * self.image_width_limit / size.width()))
        is_vector: bool = path.lower().endswith(".svg")
        if is_vector:
            reader.setScaledSize(target * ratio)
        image: QImage = reader.read()
        if image.isNull() or target == size:
            return image
        if not is_vector:
            image = image.scaled(target * ratio, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image.setDevicePixelRatio(ratio)
        return image

    def mark_matches(self, query: str) -> None:
        selections: list[QTextEdit.ExtraSelection] = []
        if query:
            highlight = QTextCharFormat()
            highlight.setBackground(QColor("#ffe58a"))
            for position, text in read_blocks(self.document()):
                for offset in match_offsets(text, query):
                    selection = QTextEdit.ExtraSelection()
                    selection.cursor = QTextCursor(self.document())
                    selection.cursor.setPosition(position + offset)
                    selection.cursor.setPosition(position + offset + len(query), QTextCursor.MoveMode.KeepAnchor)
                    selection.format = highlight
                    selections.append(selection)
        self.setExtraSelections(selections)

    def select_match(self, query: str, ordinal: int) -> None:
        passed: int = 0
        for position, text in read_blocks(self.document()):
            offsets: list[int] = match_offsets(text, query)
            if ordinal < passed + len(offsets):
                cursor = QTextCursor(self.document())
                cursor.setPosition(position + offsets[ordinal - passed])
                cursor.setPosition(cursor.position() + len(query), QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(cursor)
                self.ensureCursorVisible()
                return
            passed += len(offsets)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.rescale_timer.start()

    def rescale_images(self) -> None:
        if not self.source().isValid() or self.available_image_width() == self.image_width_limit:
            return
        bar = self.verticalScrollBar()
        position: float = bar.value() / bar.maximum() if bar.maximum() else 0
        self.reload()
        bar.setValue(round(position * bar.maximum()))


class ManualDialog(QDialog):
    START_FILE = "00-how-to-use.html"
    SEARCH_MIN_LENGTH = 2
    SEARCH_RESULT_LIMIT = 200
    SEARCH_DELAY_MS = 300

    def __init__(self, settings_handler: SettingsHandler, parent: QWidget | None = None):
        super().__init__(parent)
        self.sh: SettingsHandler = settings_handler
        self.setWindowTitle("Справка")
        self.setWindowFlag(Qt.WindowType.WindowMinMaxButtonsHint, True)
        self.resize(1150, 780)
        self.chapter_items: dict[str, QTreeWidgetItem] = {}
        self.syncing_tree: bool = False
        self.is_page_opened: bool = False
        self.search_index: dict[str, list[tuple[int, str]]] = {}

        self.trw_contents = QTreeWidget(self)
        self.trw_contents.setHeaderHidden(True)
        self.trw_contents.setIndentation(14)
        self.trw_contents.setWordWrap(True)
        self.trw_contents.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.trw_contents.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.le_search = QLineEdit(self)
        self.le_search.setPlaceholderText("Поиск по руководству (Ctrl+Shift+F)")
        self.le_search.setClearButtonEnabled(True)
        self.la_found = QLabel(self)
        self.la_found.setVisible(False)
        self.lw_results = QListWidget(self)
        self.lw_results.setItemDelegate(SearchResultDelegate(self.lw_results))
        self.lw_results.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lw_results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.stw_left = QStackedWidget(self)
        self.stw_left.addWidget(self.trw_contents)
        self.stw_left.addWidget(self.lw_results)
        left_pane = QWidget(self)
        left_pane.setMinimumWidth(180)
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.le_search)
        left_layout.addWidget(self.la_found)
        left_layout.addWidget(self.stw_left, 1)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(self.SEARCH_DELAY_MS)
        self.browser = ManualBrowser(self)

        self.tb_back = QToolButton(self)
        self.tb_back.setIcon(QIcon(":/designer/icons/left.svg"))
        self.tb_back.setToolTip("Назад (Alt+←)")
        self.tb_forward = QToolButton(self)
        self.tb_forward.setIcon(QIcon(":/designer/icons/right.svg"))
        self.tb_forward.setToolTip("Вперёд (Alt+→)")
        self.tb_back.setEnabled(False)
        self.tb_forward.setEnabled(False)
        self.la_chapter = QLabel(self)
        chapter_font: QFont = self.la_chapter.font()
        chapter_font.setBold(True)
        self.la_chapter.setFont(chapter_font)
        self.le_find = QLineEdit(self)
        self.le_find.setPlaceholderText("Поиск на странице (Ctrl+F)")
        self.le_find.setClearButtonEnabled(True)
        self.le_find.setFixedWidth(240)
        self.la_notfound = QLabel("Ничего не найдено", self)
        self.la_notfound.setStyleSheet("color: #C62828;")
        self.la_notfound.setVisible(False)
        self.tb_findprev = QToolButton(self)
        self.tb_findprev.setArrowType(Qt.ArrowType.UpArrow)
        self.tb_findprev.setToolTip("Предыдущее совпадение (Shift+F3)")
        self.tb_findnext = QToolButton(self)
        self.tb_findnext.setArrowType(Qt.ArrowType.DownArrow)
        self.tb_findnext.setToolTip("Следующее совпадение (F3, Enter)")

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.tb_back)
        top_bar.addWidget(self.tb_forward)
        top_bar.addWidget(self.la_chapter, 1)
        top_bar.addWidget(self.la_notfound)
        top_bar.addWidget(self.le_find)
        top_bar.addWidget(self.tb_findprev)
        top_bar.addWidget(self.tb_findnext)
        right_pane = QWidget(self)
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addLayout(top_bar)
        right_layout.addWidget(self.browser, 1)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.addWidget(left_pane)
        self.splitter.addWidget(right_pane)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setChildrenCollapsible(False)
        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)

        self.fill_contents()
        self.restore_layout()

        self.trw_contents.currentItemChanged.connect(self.on_contents_item_changed)
        self.trw_contents.itemClicked.connect(self.on_contents_item_clicked)
        self.splitter.splitterMoved.connect(self.trw_contents.scheduleDelayedItemsLayout)
        self.splitter.splitterMoved.connect(self.lw_results.scheduleDelayedItemsLayout)
        self.le_search.textChanged.connect(lambda: self.search_timer.start())
        self.search_timer.timeout.connect(self.run_search)
        self.lw_results.currentItemChanged.connect(lambda item: self.go_to_result(item))
        self.lw_results.itemClicked.connect(self.go_to_result)
        self.browser.sourceChanged.connect(self.on_source_changed)
        self.browser.backwardAvailable.connect(self.tb_back.setEnabled)
        self.browser.forwardAvailable.connect(self.tb_forward.setEnabled)
        self.tb_back.clicked.connect(self.browser.backward)
        self.tb_forward.clicked.connect(self.browser.forward)
        self.le_find.textChanged.connect(lambda: self.find_text(from_selection_start=True))
        self.le_find.returnPressed.connect(self.find_text)
        self.tb_findnext.clicked.connect(self.find_text)
        self.tb_findprev.clicked.connect(lambda: self.find_text(backward=True))
        QShortcut(QKeySequence.StandardKey.Find, self, self.focus_find)
        QShortcut(QKeySequence("Ctrl+Shift+F"), self, self.focus_search)
        QShortcut(QKeySequence("F3"), self, self.find_text)
        QShortcut(QKeySequence("Shift+F3"), self, lambda: self.find_text(backward=True))

    @staticmethod
    def is_available() -> bool:
        return os.path.isfile(os.path.join(manual_dir(), "contents.json"))

    def fill_contents(self) -> None:
        with open(os.path.join(manual_dir(), "contents.json"), encoding="utf-8") as file:
            groups: list[dict] = json.load(file)["groups"]
        group_font: QFont = self.trw_contents.font()
        group_font.setBold(True)
        for group in groups:
            group_item = QTreeWidgetItem(self.trw_contents, [group["title"]])
            group_item.setFont(0, group_font)
            group_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            for chapter in group["chapters"]:
                chapter_item = QTreeWidgetItem(group_item, [chapter["title"]])
                chapter_item.setToolTip(0, chapter["title"])
                chapter_item.setData(0, Qt.ItemDataRole.UserRole, (chapter["file"], ""))
                self.chapter_items[chapter["file"]] = chapter_item
                for heading in chapter["headings"]:
                    heading_item = QTreeWidgetItem(chapter_item, [heading["title"]])
                    heading_item.setData(0, Qt.ItemDataRole.UserRole, (chapter["file"], heading["anchor"]))
            group_item.setExpanded(True)

    def open_page(self, file: str = "", anchor: str = "") -> None:
        url: QUrl = QUrl.fromLocalFile(os.path.join(manual_dir(), file or self.START_FILE))
        if anchor:
            url.setFragment(anchor)
        self.is_page_opened = True
        self.browser.setSource(url)

    def show_manual(self, file: str = "", anchor: str = "") -> None:
        self.show()
        self.trw_contents.scheduleDelayedItemsLayout()
        if file or not self.is_page_opened:
            QTimer.singleShot(0, lambda: self.open_page(file, anchor))
        self.raise_()
        self.activateWindow()

    def on_contents_item_clicked(self, item: QTreeWidgetItem) -> None:
        if item.parent() is None:
            item.setExpanded(not item.isExpanded())
        else:
            QTimer.singleShot(0, lambda: self.go_to_item(item))

    def on_contents_item_changed(self, item: QTreeWidgetItem | None) -> None:
        if item is not None and not self.syncing_tree and QApplication.mouseButtons() == Qt.MouseButton.NoButton:
            QTimer.singleShot(0, lambda: self.go_to_item(item))

    def go_to_item(self, item: QTreeWidgetItem) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None:
            return
        file, anchor = data
        source: QUrl = self.browser.source()
        if source.fileName() != file or source.fragment() != anchor:
            self.open_page(file, anchor)
        elif anchor:
            self.browser.scrollToAnchor(anchor)
        else:
            self.browser.verticalScrollBar().setValue(0)

    def on_source_changed(self, url: QUrl) -> None:
        chapter_item: QTreeWidgetItem | None = self.chapter_items.get(url.fileName())
        if chapter_item is None:
            return
        self.syncing_tree = True
        try:
            for item in self.chapter_items.values():
                item.setExpanded(item is chapter_item)
            current: QTreeWidgetItem = chapter_item
            for index in range(chapter_item.childCount()):
                heading_item = chapter_item.child(index)
                if heading_item.data(0, Qt.ItemDataRole.UserRole)[1] == url.fragment():
                    current = heading_item
            self.trw_contents.setCurrentItem(current)
            self.trw_contents.scrollToItem(current)
        finally:
            self.syncing_tree = False
        self.la_chapter.setText(chapter_item.text(0))
        self.la_notfound.setVisible(False)
        self.browser.mark_matches(self.search_query())

    def search_query(self) -> str:
        query: str = normalize_text(self.le_search.text().strip())
        return query if len(query) >= self.SEARCH_MIN_LENGTH else ""

    def ensure_search_index(self) -> None:
        if self.search_index:
            return
        for file in self.chapter_items:
            document = QTextDocument()
            with open(os.path.join(manual_dir(), file), encoding="utf-8") as page:
                document.setHtml(page.read())
            self.search_index[file] = read_blocks(document)

    def run_search(self) -> None:
        query: str = self.search_query()
        self.browser.mark_matches(query)
        self.lw_results.clear()
        self.la_found.setVisible(bool(query))
        if not query:
            self.stw_left.setCurrentWidget(self.trw_contents)
            return
        self.ensure_search_index()
        found: int = 0
        for file, blocks in self.search_index.items():
            ordinal: int = 0
            for position, text in blocks:
                offsets: list[int] = match_offsets(text, query)
                ordinal += len(offsets)
                if not offsets:
                    continue
                found += 1
                if found <= self.SEARCH_RESULT_LIMIT:
                    start: int = max(0, offsets[0] - 40)
                    end: int = offsets[0] + len(query)
                    snippet: str = (f'{"…" if start else ""}{html.escape(text[start:offsets[0]])}'
                                    f'<span style="background-color: #ffe58a;"><b>{html.escape(text[offsets[0]:end])}</b></span>'
                                    f'{html.escape(text[end:end + 70])}{"…" if end + 70 < len(text) else ""}')
                    item = QListWidgetItem(self.lw_results)
                    item.setData(SearchResultDelegate.HTML_ROLE, f"<b>{html.escape(self.chapter_items[file].text(0))}</b><br>{snippet}")
                    item.setToolTip(text)
                    item.setData(Qt.ItemDataRole.UserRole, (file, ordinal - len(offsets), query))
        self.stw_left.setCurrentWidget(self.lw_results)
        self.lw_results.scheduleDelayedItemsLayout()
        if not found:
            self.la_found.setText("Ничего не найдено")
        elif found > self.SEARCH_RESULT_LIMIT:
            self.la_found.setText(f"Найдено: {found}, показаны первые {self.SEARCH_RESULT_LIMIT}")
        else:
            self.la_found.setText(f"Найдено: {found}")

    def go_to_result(self, item: QListWidgetItem | None) -> None:
        data = item.data(Qt.ItemDataRole.UserRole) if item else None
        if data is None:
            return
        file, ordinal, query = data
        if self.browser.source().fileName() != file:
            self.open_page(file)
        self.browser.select_match(query, ordinal)

    def focus_search(self) -> None:
        self.le_search.setFocus()
        self.le_search.selectAll()

    def focus_find(self) -> None:
        self.le_find.setFocus()
        self.le_find.selectAll()

    def find_text(self, backward: bool = False, from_selection_start: bool = False) -> None:
        text: str = self.le_find.text()
        cursor = self.browser.textCursor()
        if not text:
            cursor.clearSelection()
            self.browser.setTextCursor(cursor)
            self.la_notfound.setVisible(False)
            return
        if from_selection_start:
            cursor.setPosition(cursor.selectionStart())
            self.browser.setTextCursor(cursor)
        options = QTextDocument.FindFlag.FindBackward if backward else QTextDocument.FindFlag(0)
        found: bool = self.browser.find(text, options)
        if not found:
            self.browser.moveCursor(QTextCursor.MoveOperation.End if backward else QTextCursor.MoveOperation.Start)
            found = self.browser.find(text, options)
        self.la_notfound.setVisible(not found)

    def set_owner(self, owner: QWidget) -> None:
        if owner is self.parentWidget():
            return
        was_visible: bool = self.isVisible()
        self.setParent(owner, self.windowFlags())
        if isinstance(owner, QDialog):
            owner.finished.connect(lambda: self.release_owner(owner))
        if was_visible:
            self.show()

    def release_owner(self, owner: QWidget) -> None:
        if self.parentWidget() is owner and owner.parentWidget() is not None:
            self.set_owner(owner.parentWidget().window())

    def restore_layout(self) -> None:
        geometry = self.sh.settings.value("Manual/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        self.splitter.setSizes([330, 820])
        state = self.sh.settings.value("Manual/splitter")
        if state:
            self.splitter.restoreState(state)

    def save_layout(self) -> None:
        self.sh.settings.setValue("Manual/geometry", self.saveGeometry())
        self.sh.settings.setValue("Manual/splitter", self.splitter.saveState())

    def done(self, result: int) -> None:
        self.save_layout()
        super().done(result)


def open_manual(owner: QWidget, page: str = "") -> None:
    if is_viewer():
        return
    main_window: QWidget = owner
    while main_window.parentWidget() is not None:
        main_window = main_window.parentWidget()
    open_dialog = getattr(main_window, "open_manual_dialog", None)
    if open_dialog is not None:
        open_dialog(page, owner)


def add_help_shortcut(dialog: QDialog, page: str) -> None:
    if is_viewer():
        return
    QShortcut(QKeySequence("F1"), dialog, lambda: open_manual(dialog, page))
