import sys
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                              QTableWidgetItem, QFrame, QLabel, QSplitter,
                              QHeaderView, QAbstractItemView, QStyledItemDelegate, QSlider)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QBrush, QPen, QKeySequence

logger = logging.getLogger(__name__)

class CustomTableWidget(QTableWidget):
    def __init__(self, rows, cols, parent=None):
        super().__init__(rows, cols, parent)
        # 右クリックメニューでコピー・ペーストを可能にする
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QMenu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        
    def setVerticalHeaderLabels(self, labels):
        for i, label in enumerate(labels):
            item = QTableWidgetItem(label)
            self.setVerticalHeaderItem(i, item)

    def keyPressEvent(self, event):
        # Ctrl+Vで大量貼り付け時にテーブルを自動拡張する
        from PySide6.QtWidgets import QApplication
        if event.matches(QKeySequence.Paste):
            text = QApplication.clipboard().text()
            rows = text.splitlines()
            logger.debug(f"Paste detected with {len(rows)} rows")
            max_cols = max((len(r.split('\t')) for r in rows), default=0)
            cur_r = max(self.currentRow(), 0)
            cur_c = max(self.currentColumn(), 0)
            need_rows = cur_r + len(rows) - self.rowCount()
            need_cols = cur_c + max_cols - self.columnCount()
            if need_rows > 0 or need_cols > 0:
                new_r = self.rowCount() + max(need_rows, 0)
                new_c = self.columnCount() + max(need_cols, 0)
                logger.debug(f"Resizing table for paste from ({self.rowCount()},{self.columnCount()}) to ({new_r},{new_c})")
                self.setRowCount(new_r)
                self.setColumnCount(new_c)
            # データをセルに設定
            for dr, rowdata in enumerate(rows):
                for dc, val in enumerate(rowdata.split('\t')):
                    self.setItem(cur_r + dr, cur_c + dc, QTableWidgetItem(val))
            return
        super().keyPressEvent(event)

    def open_context_menu(self, position):
        """右クリックメニューを表示し、コピー・ペーストを提供する"""
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        copy_act = menu.addAction("コピー")
        paste_act = menu.addAction("ペースト")
        action = menu.exec(self.viewport().mapToGlobal(position))
        if action == copy_act:
            logger.debug("ContextMenu: コピー選択")
            self.copy_selection()
        elif action == paste_act:
            logger.debug("ContextMenu: ペースト選択")
            self.paste_clipboard()

    def copy_selection(self):
        """選択セルの内容をクリップボードにコピーする"""
        from PySide6.QtWidgets import QApplication
        ranges = self.selectedRanges()
        if not ranges:
            return
        rng = ranges[0]
        copied_rows = []
        for row in range(rng.topRow(), rng.bottomRow() + 1):
            cells = []
            for col in range(rng.leftColumn(), rng.rightColumn() + 1):
                item = self.item(row, col)
                cells.append(item.text() if item and item.text() else "")
            copied_rows.append("\t".join(cells))
        QApplication.clipboard().setText("\n".join(copied_rows))

    def paste_clipboard(self):
        """クリップボードのテキストを現在の位置にペーストし、必要に応じてテーブルを拡張する"""
        from PySide6.QtWidgets import QApplication, QTableWidgetItem
        text = QApplication.clipboard().text()
        if not text:
            return
        rows = text.splitlines()
        max_cols = max(len(r.split('\t')) for r in rows)
        cur_r = max(self.currentRow(), 0)
        cur_c = max(self.currentColumn(), 0)
        need_rows = cur_r + len(rows) - self.rowCount()
        need_cols = cur_c + max_cols - self.columnCount()
        if need_rows > 0 or need_cols > 0:
            new_r = self.rowCount() + max(need_rows, 0)
            new_c = self.columnCount() + max(need_cols, 0)
            logger.debug(f"ContextMenuでのペーストに伴うサイズ変更: ({self.rowCount()},{self.columnCount()}) -> ({new_r},{new_c})")
            self.setRowCount(new_r)
            self.setColumnCount(new_c)
        for dr, line in enumerate(rows):
            for dc, val in enumerate(line.split('\t')):
                self.setItem(cur_r + dr, cur_c + dc, QTableWidgetItem(val))

class BorderDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        text = index.data(Qt.DisplayRole)
        if index.column() == 1 and not text:
            painter.save()
            pen = QPen(QColor(75, 145, 139))  # 目に優しい深いティール色
            pen.setWidth(2)
            painter.setPen(pen)
            rect = option.rect.adjusted(1, 1, -1, -1)
            painter.drawRect(rect)
            painter.restore()

# サンプルテーブルの未入力セル表示用デリゲート
class SampleBorderDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        text = index.data(Qt.DisplayRole)
        # ヘッダーの項目名＝???は未入力として緑枠
        if index.row() == 0 and text and "???" in text:
            painter.save()
            pen = QPen(QColor(75, 145, 139))  # 目に優しい深いティール色
            pen.setWidth(2)
            painter.setPen(pen)
            rect = option.rect.adjusted(1, 1, -1, -1)
            painter.drawRect(rect)
            painter.restore()
        # サンプルデータ1行目のA-Bセルが未入力の場合は緑枠 (C列は除外)
        elif index.row() == 1 and index.column() in [1, 2] and not text:
            painter.save()
            pen = QPen(QColor(75, 145, 139))  # 目に優しい深いティール色
            pen.setWidth(2)
            painter.setPen(pen)
            rect = option.rect.adjusted(1, 1, -1, -1)
            painter.drawRect(rect)
            painter.restore()

class ExcelPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """エクセルパネルのUI設定"""
        # レイアウト設定
        self.setStyleSheet("background-color: #F5F7FA;")  # より柔らかい背景色
        excel_layout = QVBoxLayout(self)
        excel_layout.setContentsMargins(0, 0, 0, 0)
        
        # 垂直スプリッター (上下のテーブルを分割するため)
        v_splitter = QSplitter(Qt.Vertical)
        
        # 上部テーブル (サンプルデータ用) とラベルを横に並べるレイアウト
        sample_container = QWidget()
        sample_layout = QHBoxLayout(sample_container)
        sample_layout.setContentsMargins(0, 0, 0, 0)
        
        # サンプルパネル用ラベル（縦書き）
        sample_label = QLabel("テンプレ｜ト")
        sample_label.setAlignment(Qt.AlignCenter)
        sample_label.setStyleSheet("background-color: #E8EEF4; border: 1px solid #D1D9E6; padding: 5px; color: #3A506B; font-weight: bold;")
        # 縦書きにするために回転
        sample_label.setFixedWidth(25)
        sample_label.setMinimumHeight(120)
        # 90度回転させて縦書きにする
        sample_label.setWordWrap(True)
        vertical_text = "\n".join(list("テンプレ｜ト"))
        sample_label.setText(vertical_text)
        
        # 上部テーブル（サンプルデータ用）
        self.sample_table = CustomTableWidget(4, 12)  # ヘッダー行 + サンプルデータ行3行
        self.sample_table.setHorizontalHeaderLabels(["", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"])
        self.setup_table_style(self.sample_table)
        # サンプルテーブルの未入力セル表示用デリゲート設定
        self.sample_table.setItemDelegate(SampleBorderDelegate(self.sample_table))
        
        # ラベルとテーブルを水平レイアウトに追加
        sample_layout.addWidget(sample_label)
        sample_layout.addWidget(self.sample_table)
        
        # 下部テーブル (実データ用) とラベルを横に並べるレイアウト
        data_container = QWidget()
        data_layout = QHBoxLayout(data_container)
        data_layout.setContentsMargins(0, 0, 0, 0)
        
        # 実データ用ラベル（縦書き）
        data_label = QLabel("デ｜タ入力エリア")
        data_label.setAlignment(Qt.AlignCenter)
        data_label.setStyleSheet("background-color: #E8EEF4; border: 1px solid #D1D9E6; padding: 5px; color: #5D4A66; font-weight: bold;")
        data_label.setFixedWidth(25)
        data_label.setMinimumHeight(180)
        # 縦書きにする
        data_label.setWordWrap(True)
        vertical_text = "\n".join(list("デ｜タ入力エリア"))
        data_label.setText(vertical_text)
        
        # 下部テーブル (実データ用)
        self.data_table = CustomTableWidget(13, 12)  # 実データ用の行数
        # 横ヘッダーをA-Kまで設定
        self.data_table.setHorizontalHeaderLabels(["", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"])
        # テーブルスタイルを適用
        self.setup_table_style(self.data_table)
        # 元の値列の未入力セル表示用デリゲート設定
        self.data_table.setItemDelegateForColumn(1, BorderDelegate(self.data_table))
        
        # ラベルとテーブルを水平レイアウトに追加
        data_layout.addWidget(data_label)
        data_layout.addWidget(self.data_table)
        
        # スプリッターに上下のコンテナを追加
        v_splitter.addWidget(sample_container)
        v_splitter.addWidget(data_container)
        
        # スプリッターの初期サイズ比率を設定 (上:下 = 3:7)
        v_splitter.setSizes([300, 700])
        
        # 両方のテーブルの選択モードを1行全体選択に設定
        self.sample_table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectItems)
        
        excel_layout.addWidget(v_splitter)
        
        # 状態表示パネル
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.StyledPanel)
        status_frame.setStyleSheet("background-color: #EFF2F7; border: 1px solid #D1D9E6;")
        status_layout = QHBoxLayout(status_frame)
        
        # 色の説明をシンプルに
        color_explanation = QWidget()
        color_explanation.setStyleSheet("background-color: transparent;")
        color_layout = QHBoxLayout(color_explanation)
        color_layout.setContentsMargins(5, 5, 5, 5)
        
        # 色の凡例
        legends = [
            ("未入力", QColor(255, 255, 255), QColor(0, 0, 0)), 
            ("入力済み", QColor(245, 245, 245), QColor(0, 0, 0)), 
            ("入力不可", QColor(220, 220, 220), QColor(0, 0, 0)), 
            ("AI入力予定", QColor(220, 245, 235), QColor(0, 0, 0))  # 青みが強い淡いブルーグリーン
        ]
        
        for text, bg_color, text_color in legends:
            # 色サンプル
            color_sample = QFrame()
            color_sample.setFixedSize(20, 20)
            # 未入力は緑枠、それ以外は灰色枠
            if text == "未入力":
                color_sample.setStyleSheet(
                    f"background-color: {bg_color.name()}; border: 1px solid #4B918B;"  # 目に優しい深いティール色
                )
            else:
                color_sample.setStyleSheet(
                    f"background-color: {bg_color.name()}; border: 1px solid #D1D9E6;"  # より柔らかい枠線色
                )
            
            # テキスト
            label = QLabel(text)
            label.setStyleSheet(f"color: #000000; background-color: transparent;")
            
            # 水平レイアウトに追加
            legend_layout = QHBoxLayout()
            legend_layout.addWidget(color_sample)
            legend_layout.addWidget(label)
            legend_layout.addSpacing(10)  # 間隔
            
            color_layout.addLayout(legend_layout)
        
        color_layout.addStretch()
        status_layout.addWidget(color_explanation)
        
        # フォントサイズ調整スライダー
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(8, 24)
        self.font_size_slider.setValue(10)
        self.font_size_slider.setFixedWidth(100)
        self.font_size_slider.setToolTip("フォントサイズ")
        self.font_size_slider.valueChanged.connect(self.on_font_size_changed)
        status_layout.addStretch()
        status_layout.addWidget(self.font_size_slider)
        
        excel_layout.addWidget(status_frame)
        
        # データを設定
        self.setup_sample_data()
        # ルール未設定時のデフォルト表示: ヘッダー行のみを設定し、サンプル行をクリア
        default_headers = ["AIの進捗", "元の値", "項目名＝???", ""]
        for col, text in enumerate(default_headers):
            item = QTableWidgetItem(text)
            if col in [0, 1]:
                bgcolor = QColor(220, 220, 220)
            else:
                bgcolor = QColor(245, 245, 245)
            item.setBackground(QBrush(bgcolor))
            item.setForeground(QBrush(QColor(0, 0, 0)))
            item.setFont(QFont("Arial", 10, QFont.Bold))
            self.sample_table.setItem(0, col, item)
        # default_headersで上書きしなかった余分なヘッダーセル（以前のsetup_sample_dataの残り）をクリア
        for col in range(len(default_headers), self.sample_table.columnCount()):
            self.sample_table.setItem(0, col, QTableWidgetItem(""))
        # 下部テーブルにも同じデフォルトヘッダーを設定し、余分なセルをクリア
        for col, text in enumerate(default_headers):
            item = QTableWidgetItem(text)
            # col0-1は入力不可色、その他は薄いグレー
            bgcolor = QColor(220, 220, 220) if col in [0, 1] else QColor(245, 245, 245)
            item.setBackground(QBrush(bgcolor))
            item.setForeground(QBrush(QColor(0, 0, 0)))
            item.setFont(QFont("Arial", 10, QFont.Bold))
            self.data_table.setItem(0, col, item)
        # 余分なヘッダーセルをクリア
        for col in range(len(default_headers), self.data_table.columnCount()):
            self.data_table.setItem(0, col, QTableWidgetItem(""))
        # 下部テーブルのヘッダー行を編集不可にする
        for col in range(self.data_table.columnCount()):
            item = self.data_table.item(0, col)
            if item:
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
        # サンプルデータ行（1行目以降）を空文字でクリア
        for row in range(1, self.sample_table.rowCount()):
            for col in range(self.sample_table.columnCount()):
                self.sample_table.setItem(row, col, QTableWidgetItem(""))
        # 上部テーブルのAI進捗列を入力不可に設定し、背景色を濃いグレーに設定
        for row in range(self.sample_table.rowCount()):
            item = self.sample_table.item(row, 0)
            if item:
                item.setBackground(QBrush(QColor(220, 220, 220)))
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
    
    def setup_table_style(self, table):
        """テーブルのスタイル設定を行う共通メソッド"""
        table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                color: #333333;
                gridline-color: #D1D9E6;
            }
            QTableWidget::item:selected {
                background-color: #E8EEF4;
                color: #3A506B;
            }
            QHeaderView {
                background-color: #E8EEF4;
            }
            QHeaderView::section {
                background-color: #E8EEF4;
                color: #3A506B;
                border: 1px solid #D1D9E6;
            }
        """)
        table.horizontalHeader().setFixedHeight(30)
        table.horizontalHeader().setStretchLastSection(False)
        # デフォルトの列幅を80から120に変更
        table.horizontalHeader().setDefaultSectionSize(120)
        # 最初の列の幅を40から60に変更
        table.setColumnWidth(0, 60)  # チェックマーク列の幅を固定
    
    def setup_sample_data(self):
        """サンプルデータの設定"""
        # サンプルテーブルの行ヘッダー設定
        sample_headers = ["", "1", "2", "3"]
        self.sample_table.setVerticalHeaderLabels(sample_headers)
        
        # 実データテーブルの行ヘッダー設定
        data_headers = [""]  # ヘッダー行は空
        for i in range(1, 13):
            data_headers.append(str(i))
        self.data_table.setVerticalHeaderLabels(data_headers)
        
        # サンプルテーブルの見出し行（0行目）
        header_texts = ["AIの進捗", "元の値", "項目名＝名字", "項目名＝下の名前", "項目名＝よみがな"]
        
        for col, text in enumerate(header_texts):
            item = QTableWidgetItem(text)
            # 上部パネルのヘッダー色調整
            # col0(AIの進捗), col1(元の値) -> 入力不可（濃いグレー）
            # col2-4(項目名)  -> 入力可（薄いグレー）
            if col in [0, 1]:
                bgcolor = QColor(220, 220, 220)
            else:
                bgcolor = QColor(245, 245, 245)
            item.setBackground(QBrush(bgcolor))
            item.setForeground(QBrush(QColor(0, 0, 0)))
            item.setFont(QFont("Arial", 10, QFont.Bold))
            self.sample_table.setItem(0, col, item)
        
        # サンプルデータ行（1-2行目）
        sample_data = [
            ["ルール完成", "山田太郎", "山田", "太郎", "ヤマダタロウ"],
            ["ルール完成", "鈴木花子", "鈴木", "花子", "スズキハナコ"],
        ]
        
        for row, data in enumerate(sample_data, start=1):
            # サンプルデータのセル
            for col, text in enumerate(data):
                item = QTableWidgetItem(text)
                # 列によって背景色を変える
                if col == 0:  # AIの進捗列
                    item.setBackground(QBrush(QColor(220, 220, 220)))  # 入力不可（グレー）
                    item.setTextAlignment(Qt.AlignCenter)  # センター揃え
                elif col == 1:  # 元の値列
                    item.setBackground(QBrush(QColor(245, 245, 245)))  # 薄いグレー
                else:  # 処理結果列
                    # 値が入っているので入力済みとする
                    item.setBackground(QBrush(QColor(245, 245, 245)))  # 薄いグレー
                
                item.setForeground(QBrush(QColor(0, 0, 0)))  # 黒色テキスト
                self.sample_table.setItem(row, col, item)
        
        # 実データテーブルに見出し行を追加（データテーブルの0行目）：上部のヘッダーを参照
        for col in range(len(header_texts)):
            sample_item = self.sample_table.item(0, col)
            header_text = sample_item.text() if sample_item else ""
            item = QTableWidgetItem(header_text)
            # 下部パネルのヘッダーはすべて入力不可（濃いグレー）
            item.setBackground(QBrush(QColor(220, 220, 220)))
            item.setForeground(QBrush(QColor(0, 0, 0)))
            item.setFont(QFont("Arial", 10, QFont.Bold))
            self.data_table.setItem(0, col, item)

        # --- 実データテーブルのデータと色分け設定 ---
        # AI入力予定列の最大インデックスを取得 (NameError防止)
        valid_item_cols = [col for col in range(2, self.sample_table.columnCount())
                            if self.sample_table.item(0, col) and self.sample_table.item(0, col).text()]
        max_item_col = max(valid_item_cols) if valid_item_cols else 1
        initial_data_text = {}

        for row in range(1, 13):  # データ行 (1から12まで)
            for col in range(12):  # 全列 (0から11まで)
                text = initial_data_text.get((row, col), "") # 初期テキスト取得
                item = QTableWidgetItem(text)
                
                # デフォルトの文字色は黒
                item.setForeground(QBrush(QColor(0, 0, 0)))

                # 列に基づいて背景色とスタイルを設定
                if col == 0:  # AIの進捗列 (入力不可)
                    item.setBackground(QBrush(QColor(220, 220, 220)))  # グレー
                    item.setTextAlignment(Qt.AlignCenter)
                    if text == "✗":
                        item.setForeground(QBrush(QColor(255, 0, 0)))  # 赤色
                elif col == 1:  # 元の値列 (B列)
                    # テキストが空かどうかで判定
                    if text: # テキストがあれば入力済み
                        item.setBackground(QBrush(QColor(245, 245, 245)))  # 薄いグレー
                    else: # テキストがなければ未入力
                        item.setBackground(QBrush(QColor(255, 255, 255)))  # 白
                elif 2 <= col <= max_item_col:
                    header_item = self.sample_table.item(0, col)
                    if header_item and header_item.text():
                        item.setBackground(QBrush(QColor(220, 245, 235)))  # 青みが強い淡いブルーグリーン
                    else:
                        item.setBackground(QBrush(QColor(220, 220, 220)))
                else:
                    item.setBackground(QBrush(QColor(255, 255, 255)))

                self.data_table.setItem(row, col, item)
        
        # 両方のテーブルの最初の行を固定表示
        self.sample_table.setRowHidden(0, False)
        self.sample_table.verticalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        
        self.data_table.setRowHidden(0, False)
        self.data_table.verticalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        
        # AI進捗列と下パネルの項目行を入力不可にする
        for table in (self.sample_table, self.data_table):
            for row in range(table.rowCount()):
                item = table.item(row, 0)
                if item:
                    # 選択および編集不可フラグを設定
                    item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
        # 下パネルの項目行（0行目）を入力不可に設定
        for col in range(self.data_table.columnCount()):
            item = self.data_table.item(0, col)
            if item:
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
    
    def simulate_processing(self, table, row):
        logger.debug(f"simulate_processing start: table={table.objectName() if table.objectName() else table}, row={row}")
        """処理のシミュレーション"""
        # 元データが存在するか確認 - 元の値列（インデックス1）を確認
        original_item = table.item(row, 1)  # 元の値列はインデックス1
        if original_item:
            logger.debug(f"original_item.text(): '{original_item.text()}'")
        if original_item and original_item.text():
            logger.debug(f"processing row {row} started")
            # チェックマークを追加
            check_item = QTableWidgetItem("✓")
            check_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 0, check_item)
            logger.debug(f"checkmark set for row {row}")
            
            # 処理結果の背景色を処理済みに変更
            for col in range(2, table.columnCount()):  # 処理結果列（インデックス2から最後の列まで）
                item = table.item(row, col)
                if item:
                    item.setBackground(QBrush(QColor(220, 220, 220)))  # 入力不可（グレー）
                    item.setForeground(QBrush(QColor(0, 0, 0)))  # 黒色テキスト
            logger.debug(f"processing row {row} completed")

    def load_sample_data(self, sample_data):
        """JSONから読み込んだサンプルデータでテーブルを更新"""
        # 既存のコンテンツをクリア
        self.sample_table.clearContents()
        # ヘッダー行の設定
        headers = sample_data.get("headers", [])
        for col, text in enumerate(headers):
            item = QTableWidgetItem(text)
            if col in [0, 1]:
                bgcolor = QColor(220, 220, 220)
            else:
                bgcolor = QColor(245, 245, 245)
            item.setBackground(QBrush(bgcolor))
            item.setForeground(QBrush(QColor(0, 0, 0)))
            item.setFont(QFont("Arial", 10, QFont.Bold))
            self.sample_table.setItem(0, col, item)
        # サンプルデータ行の設定
        rows = sample_data.get("rows", [])
        for row_idx, row_vals in enumerate(rows, start=1):
            for col, text in enumerate(row_vals):
                item = QTableWidgetItem(text)
                if col == 0:
                    item.setBackground(QBrush(QColor(220, 220, 220)))
                    item.setTextAlignment(Qt.AlignCenter)
                elif col == 1:
                    item.setBackground(QBrush(QColor(245, 245, 245)))
                else:
                    item.setBackground(QBrush(QColor(245, 245, 245)))
                item.setForeground(QBrush(QColor(0, 0, 0)))
                self.sample_table.setItem(row_idx, col, item)
        # 必要に応じて追加のスタイルや列制御を行う 
        # 下パネルのヘッダー行を上パネルのヘッダー行を参照して同期
        logger.debug("load_sample_data: syncing data_table header with sample_table header")
        for col in range(self.sample_table.columnCount()):
            sample_item = self.sample_table.item(0, col)
            header_text = sample_item.text() if sample_item else ""
            item = QTableWidgetItem(header_text)
            # 下パネルのヘッダーはすべて入力不可（濃いグレー）
            item.setBackground(QBrush(QColor(220, 220, 220)))
            item.setForeground(QBrush(QColor(0, 0, 0)))
            item.setFont(QFont("Arial", 10, QFont.Bold))
            # 編集不可フラグを設定
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
            self.data_table.setItem(0, col, item) 

        # データテーブルのAI入力予定列の背景色をヘッダーに合わせて更新
        valid_item_cols = [col for col in range(2, self.sample_table.columnCount())
                            if self.sample_table.item(0, col) and self.sample_table.item(0, col).text()]
        max_item_col = max(valid_item_cols) if valid_item_cols else 1
        for row in range(1, self.data_table.rowCount()):
            for col in range(self.data_table.columnCount()):
                item = self.data_table.item(row, col)
                if not item:
                    item = QTableWidgetItem("")
                    self.data_table.setItem(row, col, item)
                # AI進捗列
                if col == 0:
                    item.setBackground(QBrush(QColor(220, 220, 220)))
                    item.setTextAlignment(Qt.AlignCenter)
                    if item.text() == "✗":
                        item.setForeground(QBrush(QColor(255, 0, 0)))
                    else:
                        item.setForeground(QBrush(QColor(0, 0, 0)))
                # 元の値列
                elif col == 1:
                    if item.text():
                        item.setBackground(QBrush(QColor(245, 245, 245)))
                    else:
                        item.setBackground(QBrush(QColor(255, 255, 255)))
                # 項目名列 (AI入力予定 or 無効) を動的に対応
                elif 2 <= col <= max_item_col:
                    header_item = self.sample_table.item(0, col)
                    if header_item and header_item.text():
                        item.setBackground(QBrush(QColor(220, 245, 235)))  # 青みが強い淡いブルーグリーン
                    else:
                        item.setBackground(QBrush(QColor(220, 220, 220)))
                # ヘッダー範囲外の列 (未入力)
                else:
                    item.setBackground(QBrush(QColor(255, 255, 255)))

    def on_font_size_changed(self, size):
        """フォントサイズ変更のハンドラ"""
        for table in (self.sample_table, self.data_table):
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item:
                        font = item.font()
                        font.setPointSize(size)
                        item.setFont(font)

    def get_excel_column_labels(self, count: int) -> list[str]:
        """1から始まる列数に対応したExcelライクな列名リストを返す。count は列数(A列が1)を指定。"""
        labels: list[str] = []
        for i in range(count):  # 0-based 内部計算
            n = i
            s = ''
            while True:
                s = chr(ord('A') + (n % 26)) + s
                n = n // 26 - 1
                if n < 0:
                    break
            labels.append(s)
        return labels

    def load_csv(self, file_path: str):
        """CSVを読み込んでデータテーブルに反映する"""
        import csv
        from PySide6.QtWidgets import QTableWidgetItem
        from PySide6.QtCore import Qt
        # CSV読み込み
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            # CSVヘッダー行は無視し、テンプレートの項目行を使用
            next(reader, None)
            rows = list(reader)
        # テーブル拡張
        old_r, old_c = self.data_table.rowCount(), self.data_table.columnCount()
        new_r = len(rows) + 1  # ヘッダー行含む
        # 列数はテンプレート(sample_table)に合わせる
        new_c = self.sample_table.columnCount()
        logger.debug(f"Expanding data_table from ({old_r},{old_c}) to ({new_r},{new_c})")
        self.data_table.setRowCount(new_r)
        self.data_table.setColumnCount(new_c)
        # リサイズ後にスタイルとデリゲートを再適用
        self.setup_table_style(self.data_table)
        # 元の値列（インデックス1）に未入力枠デリゲートを設定
        self.data_table.setItemDelegateForColumn(1, BorderDelegate(self.data_table))
        # 横ヘッダー(AI進捗列を空、以降Excelライクに生成)
        col_labels = [""] + self.get_excel_column_labels(new_c - 1)
        self.data_table.setHorizontalHeaderLabels(col_labels)
        # 縦ヘッダー(0行目はヘッダー行、それ以降は1から)
        v_labels = [""] + [str(i) for i in range(1, new_r)]
        self.data_table.setVerticalHeaderLabels(v_labels)
        # ヘッダー行はテンプレートのsample_tableヘッダーを参照して同期
        logger.debug("load_csv: syncing header with sample_table")
        for col in range(self.data_table.columnCount()):
            if col < self.sample_table.columnCount():
                sample_item = self.sample_table.item(0, col)
                header_text = sample_item.text() if sample_item else ""
            else:
                header_text = ""
            item = QTableWidgetItem(header_text)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.data_table.setItem(0, col, item)
        # データ行設定
        for r, row_vals in enumerate(rows, start=1):
            # 進捗列リセット
            chk = QTableWidgetItem("")
            chk.setTextAlignment(Qt.AlignCenter)
            self.data_table.setItem(r, 0, chk)
            # テンプレートの列数に合わせてデータをセット
            for c in range(1, self.data_table.columnCount()):
                val = row_vals[c-1] if c-1 < len(row_vals) else ""
                item = QTableWidgetItem(val)
                self.data_table.setItem(r, c, item)

    def save_csv(self, file_path: str):
        """データテーブルをCSVに保存する"""
        import csv
        # データテーブルの内容取得
        cols = self.data_table.columnCount()
        rows = self.data_table.rowCount()
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # ヘッダー行 B列以降
            headers = [self.data_table.item(0, c).text() if self.data_table.item(0, c) else '' for c in range(1, cols)]
            writer.writerow(headers)
            # データ行
            for row in range(1, rows):
                row_vals = []
                for c in range(1, cols):
                    item = self.data_table.item(row, c)
                    row_vals.append(item.text() if item else '')
                writer.writerow(row_vals)