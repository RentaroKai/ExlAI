#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ExlAIアプリケーションの起動用スクリプト"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from app.ui.integrated_ui import IntegratedExcelUI


def main():
    # ログ設定
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename='app.log',
        filemode='a'
    )
    logging.info("アプリケーション起動開始")
    try:
        app = QApplication(sys.argv)
        window = IntegratedExcelUI()
        window.show()
        logging.info("メインウィンドウを表示完了")
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"アプリケーション実行中にエラーが発生: {e}")
        raise
    finally:
        logging.info("アプリケーション終了")


if __name__ == "__main__":
    main() 