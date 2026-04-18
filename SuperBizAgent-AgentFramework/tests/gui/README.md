# GUI 宏观测试能力（可复用）

这套测试用于 Windows + Tk 桌面应用的“宏观闭环验证”：

- 启动应用
- 切换关键页面/菜单
- 断言关键文本是否出现
- 自动截图留证
- 输出 `result.json` 报告

## 1. 安装依赖

```bash
pip install pywinauto pyautogui pillow
```

## 2. 运行示例

### 2.1 直接运行 Python

```bash
py -3 tests/gui/gui_macro_runner.py --scenario tests/gui/scenarios/ops_menu_smoke.json --artifacts-dir tests/gui/artifacts/latest
```

### 2.2 PowerShell 一键运行

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-gui-macro.ps1 -Scenario "tests/gui/scenarios/main_nav_smoke.json"
```

## 3. 如何扩展场景

在 `tests/gui/scenarios/*.json` 新增文件，按步骤定义：

- `launch_app`
- `attach_main_window`
- `click_text`
- `assert_text`
- `wait`
- `screenshot`
- `close_app`

每个场景执行后会输出：

- 截图：`tests/gui/artifacts/latest/*.png`
- 报告：`tests/gui/artifacts/latest/result.json`

## 4. 闭环验收标准（建议）

- 所有步骤 `status = passed`
- 至少保留关键步骤截图（菜单切换页）
- 失败时必须附带失败截图和错误详情

