# -*- coding: utf-8 -*-
"""生成器单元测试（仅用标准库 unittest，无第三方依赖）。

运行：python tests/test_generator.py
"""

import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import generate_snake as gen  # noqa: E402


class TestGenerator(unittest.TestCase):
    def test_html_基本结构(self):
        html = gen.build_html(gen.default_cfg())
        for marker in ("<!DOCTYPE html>", "<html", "<head>", "<canvas", "</script>", "</html>"):
            self.assertIn(marker, html, marker)

    def test_html_游戏特性标记(self):
        html = gen.build_html(gen.default_cfg())
        markers = [
            "localStorage",           # 持久化（最高分/局数/历史/主题）
            "data-theme",             # 主题切换
            "snake_theme",
            "snake_high",
            "snake_games",
            "snake_history",
            "requestAnimationFrame",  # 平滑渲染循环
            "addEventListener(\"keydown\"",
            "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight",  # 方向键
        ]
        for marker in markers:
            self.assertIn(marker, html, marker)

    def test_html_界面文案标记(self):
        html = gen.build_html(gen.default_cfg())
        for marker in ("新一局", "重置", "历史", "主题", "最高分", "局数", "剩余雷数", "目标"):
            self.assertIn(marker, html, marker)

    def test_html_难度与操控标记(self):
        html = gen.build_html(gen.default_cfg())
        for marker in ("难度", "操控", "鼠标", "无尽", "DIFFICULTIES", "steerToward",
                       "reachable", "mousedown", "mousemove", "id=\"difficulty\"", "id=\"control\""):
            self.assertIn(marker, html, marker)

    def test_配置注入(self):
        html = gen.build_html(gen.default_cfg(cols=30, rows=25, target=200, maxMines=5, maxLives=4))
        # json.dumps(separators=(",", ":")) 生成紧凑格式，无空格。
        self.assertIn('"cols":30', html)
        self.assertIn('"target":200', html)
        self.assertIn('"maxMines":5', html)
        self.assertIn('"maxLives":4', html)

    def test_core_js_导出与函数(self):
        js = gen.CORE_JS
        for marker in ("module.exports", "createState", "setDirection", "tick",
                       "placeMines", "reshuffleMines", "reachable", "steerToward", "DIFFICULTIES"):
            self.assertIn(marker, js, marker)

    def test_写出文件(self):
        # 在 workspace 内建临时目录（沙箱禁止写系统临时目录）。
        tmp_root = Path(__file__).resolve().parent / "_tmp_output"
        tmp_root.mkdir(parents=True, exist_ok=True)
        try:
            out = tmp_root / "snake.html"
            core_out = tmp_root / "snake_core.js"
            gen.write_outputs(out, core_out, gen.default_cfg())
            self.assertTrue(out.exists())
            self.assertTrue(core_out.exists())
            self.assertIn("localStorage", out.read_text(encoding="utf-8"))
            self.assertIn("module.exports", core_out.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)

    def test_默认配置常量(self):
        cfg = gen.default_cfg()
        self.assertGreaterEqual(cfg["cols"], 5)
        self.assertGreaterEqual(cfg["rows"], 5)
        self.assertGreater(cfg["target"], 0)
        self.assertGreaterEqual(cfg["maxMines"], 0)
        self.assertGreater(cfg["maxLives"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
