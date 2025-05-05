import os
import json
import logging
import re
from typing import Any, Dict, List, Optional
from datetime import datetime

from utils.config import config_manager
from .gemini_api import GeminiAPI, GeminiAPIError

logger = logging.getLogger(__name__)

class RuleService:
    """
    ルール管理APIクライアントのスケルトン
    create_rule / regenerate_rule / get_rules / delete_rule / apply_rule を提供する
    """
    def __init__(self, rules_path: Optional[str] = None):
        # デフォルトのルールはUI history_rules.jsonを利用
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        default_path = os.path.join(base_dir, 'app', 'ui', 'history_rules.json')
        self.rules_path = rules_path or default_path
        self._load_rules()
        self.gemini = GeminiAPI()

    def _load_rules(self) -> None:
        """ローカルストレージからルール一覧を読み込む"""
        if os.path.exists(self.rules_path):
            try:
                with open(self.rules_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # JSON が 'rules' キーを持つ場合はその配列を利用、リストの場合はそのまま
                if isinstance(data, dict) and 'rules' in data:
                    self._rules = data['rules']
                elif isinstance(data, list):
                    self._rules = data
                else:
                    logger.warning(f"Unexpected rules format in {self.rules_path}")
                    self._rules = []
                logger.debug(f"Loaded rules from {self.rules_path}")
            except Exception as e:
                logger.error(f"Failed to load rules: {e}")
                self._rules = []
        else:
            self._rules = []

    def _save_rules(self) -> None:
        """現在のルール一覧をローカルストレージに保存する"""
        try:
            with open(self.rules_path, 'w', encoding='utf-8') as f:
                json.dump(self._rules, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved rules to {self.rules_path}")
        except Exception as e:
            logger.error(f"Failed to save rules: {e}")

    def create_rule(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        新規ルールをAIに生成させ、ローカルに保存 (3ステップ：prompt/json例/title)
        引数 samples: [{"input": str, "output": Dict[str,str], "fields": List[str]}]
        戻り値: metadata dict (rule_name, etc.)
        """
        # --- 入力サンプルをテーブル形式で構築 ---
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # fields に空文字が含まれている場合は除外する
        fields = [f for f in samples[0].get('fields', []) if f] if samples else []
        headers_init = ["AIの進捗", "元の値"] + fields
        rows_init = [["ルール完成", s.get('input','')] + [s.get('output',{}).get(f,'') for f in fields] for s in samples]
        sample_data = {"headers": headers_init, "rows": rows_init}

        # --- Phase1: 動的プロンプト生成 ---
        prompt_instructions = []
        # ヘッダー説明
        field_list = "、".join(fields)
        prompt_instructions.append(
            f"以下に示すのは、ある入力データ（「元の値」）と、それに対して特定の処理を行った結果得られた複数の出力項目（{field_list}）の具体例です。\n"
        )
        prompt_instructions.append("**データ例:**")
        # サンプルごとの例を動的に生成
        for idx, s in enumerate(samples):
            prompt_instructions.append(f"例{idx+1}")
            prompt_instructions.append(f"元の値: {s.get('input', '')}")
            for f in fields:
                prompt_instructions.append(f"項目名={f}: {s.get('output', {}).get(f, '')}")
        # 依頼部分
        prompt_instructions.append("\n**依頼:**")
        prompt_instructions.append(
            f"これらの入力（元の値）と出力（各項目）の関係性を分析し、「元の値」のようなデータを入力として与えた際に、これらの出力項目（{field_list}）を生成させるためにAIに与えるべき指示（プロンプト）を推測し、作成してください。"
        )
        prompt_instructions.append("\n生成するプロンプトの要件:")
        prompt_instructions.append("* 提示された例だけでなく、他の同様の入力に対しても適用できるような、汎用的な指示にしてください。")
        prompt_instructions.append("* プロンプトは、AIに対する指示として機能する、端的で短い文章(20文字以内)にまとめること。返答例は別途添付するためここでは端的な表現を心がけること")
        try:
            resp1 = self.gemini.client.models.generate_content(
                model=self.gemini.transcription_model,
                contents="\n".join(prompt_instructions)
            )
            rule_prompt = resp1.text.strip()
        except Exception as e:
            logger.error(f"プロンプト生成エラー: {e}")
            rule_prompt = ""

        # --- Phase2: JSONフォーマット例生成 ---
        json_instructions = [
            "このルールが出力すべきJSONフォーマットの例を示してください。",
            "応答は有効なJSON配列形式で返してください。"
        ]
        try:
            resp2 = self.gemini.client.models.generate_content(
                model=self.gemini.title_model,
                contents="\n".join(json_instructions)
            )
            json_format_example = json.loads(resp2.text)
        except Exception as e:
            logger.error(f"JSONフォーマット生成エラー: {e}")
            json_format_example = []

        # --- Phase3: タイトル生成 ---
        title_instructions = [
            "次の命令文にふさわしい短いルール名を日本語で返してください。",
            "返答は {\"rule_name\": \"<ルール名>\"} の形式で JSON のみを返し、他の文言を含めないでください。",
            f"命令文: {rule_prompt}"
        ]
        try:
            resp3 = self.gemini.client.models.generate_content(
                model=self.gemini.title_model,
                contents="\n".join(title_instructions)
            )
            # JSONパースして rule_name を取得
            text = resp3.text.strip()
            # コードブロックやバッククオートを除去
            if text.startswith("```"):
                # ```json や ``` コードブロックマーカーを削除
                text = re.sub(r"```(?:json)?\\n?", "", text)
                text = text.rstrip("`\n ")
            # JSON部分を抽出
            start = text.find("{")
            end = text.rfind("}")
            json_str = text[start:end+1] if start != -1 and end != -1 else text
            try:
                data = json.loads(json_str)
                rule_name = data.get("rule_name", "").strip()
            except Exception as e:
                logger.error(f"タイトルJSONパースエラー: {e}")
                # フォールバックで生テキストをタイトルとして使用
                rule_name = text
        except Exception as e:
            logger.error(f"タイトル生成エラー: {e}")
            rule_name = f"ルール生成 {now}"

        # --- ルールオブジェクト作成・保存 ---
        rule_obj = {
            "title": rule_name,
            "prompt": rule_prompt,
            "json_format_example": json_format_example,
            "sample_data": sample_data
        }
        # ローカルファイルに保存
        self._rules.append(rule_obj)
        self._save_rules()

        # 戻り値用メタデータ
        metadata = rule_obj.copy()
        metadata['rule_name'] = rule_name
        return metadata

    def regenerate_rule(self, rule_id: str, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        既存ルールを再生成し、更新する
        """
        # 指定ルールを検索
        updated = None
        for idx, r in enumerate(self._rules):
            if r.get('title') == rule_id:
                updated = idx
                break
        if updated is None:
            raise GeminiAPIError(f"ルール '{rule_id}' が見つかりません")
        # 新しいサンプルデータで置換
        metadata = self.create_rule(samples)
        # 古いルールを削除
        self._rules.pop(updated)
        self._save_rules()
        return metadata

    def get_rules(self) -> List[Dict[str, Any]]:
        """
        保存済みルールのメタ情報リストを返却
        """
        return self._rules

    def delete_rule(self, rule_id: str) -> bool:
        """
        指定したrule_idのルールを削除する
        成功時にTrue、失敗時にFalseを返却
        """
        for idx, r in enumerate(self._rules):
            if r.get('title') == rule_id:
                self._rules.pop(idx)
                self._save_rules()
                return True
        logger.warning(f"削除対象のルール '{rule_id}' が見つかりませんでした")
        return False

    def apply_rule(self, rule_id: str, inputs: List[str]) -> List[Dict[str, Any]]:
        """
        指定したルールを入力リストに適用し、結果を返却
        """
        # ルールを検索
        rule = next((r for r in self._rules if r.get('title') == rule_id), None)
        if not rule:
            raise GeminiAPIError(f"ルール '{rule_id}' が見つかりません")
        sample_data = rule.get('sample_data', {})
        headers = sample_data.get('headers', [])
        rows = sample_data.get('rows', [])
        results = []
        for inp in inputs:
            # マッチするサンプル行を検索
            match = next((row for row in rows if row[1] == inp), None)
            if match:
                # 出力フィールド生成
                out = {headers[i]: match[i] for i in range(2, len(headers))}
                results.append({"input": inp, "output": out, "status": "success"})
            else:
                results.append({"input": inp, "output": {}, "status": "error", "error_msg": "サンプルデータに一致しません"})
        return results 