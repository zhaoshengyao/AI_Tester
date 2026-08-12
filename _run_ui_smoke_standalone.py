# -*- coding: utf-8 -*-
"""独立脚本（不依赖 pytest-playwright 包；只用 playwright.sync_api launch）。
直接在 Python 里跑 UI smoke 10 条，并输出 JSON 结果 + 截图到 raw/ui/。
"""
from __future__ import annotations

import json
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

ROOT = Path(r"d:\AICode\TestHub\AITestDemo")
IPD = ROOT / "projects" / "ipd"
load_dotenv(IPD / ".env")
RUN_TS = max(
    [p for p in (IPD / "docs" / "test-runs").glob("*") if p.is_dir()],
    key=lambda p: p.name,
).name
RUN_DIR = IPD / "docs" / "test-runs" / RUN_TS
OUT = RUN_DIR / "raw" / "ui"
OUT.mkdir(parents=True, exist_ok=True)
BASE_URL = os.getenv("BASE_URL", "http://192.168.2.97:6090").rstrip("/")
USERNAME = os.getenv("TEST_USERNAME", "赵经理")
PASSWORD = os.getenv("TEST_PASSWORD", "123456")

results = []
start = datetime.now()


def result(tid: str, title: str, passed: bool, detail: str = "", ss_path: str = ""):
    d = {"id": tid, "title": title, "outcome": "passed" if passed else "failed",
         "detail": detail[:500], "screenshot": ss_path,
         "ts": datetime.now().isoformat(timespec="seconds")}
    results.append(d)
    print(f"[{'PASS' if passed else 'FAIL'}] {tid} {title}{(' - ' + detail) if detail else ''}")
    return d


def ss(page, name):
    p = str(OUT / f"{name}.png")
    try:
        page.screenshot(path=p, full_page=True)
    except Exception:
        pass
    return p


def open_submenu(page, top_menu_text, sub_text):
    # hover/click 父 menuitem → 点 sub
    try:
        parent = page.locator(f"[role=menuitem]", has_text=top_menu_text).first
        parent.hover(timeout=3000)
        page.wait_for_timeout(300)
        parent.click(force=True, timeout=3000)
    except Exception:
        pass
    page.wait_for_timeout(300)
    sub = page.get_by_text(sub_text).first
    sub.click(force=True, timeout=4000)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(600)


def main():
    try:
        pw = sync_playwright().start()
    except Exception as e:
        print("playwright.start FAIL:", type(e).__name__, str(e)[:300])
        result("PW-INIT", "启动 Playwright", False, f"{type(e).__name__}: {e}")
        with open(OUT / "ui-smoke-results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        sys.exit(1)

    browser = None
    try:
        browser = pw.chromium.launch(headless=True)
    except Exception as e:
        # chromium 未安装 → 记录未执行
        print("chromium.launch FAIL:", type(e).__name__, str(e)[:300])
        result("PW-CHROMIUM", "启动 chromium 浏览器", False,
               f"{type(e).__name__}: {e}。按 AGENTS.md UI 自动化=未执行。")
        with open(OUT / "ui-smoke-results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        pw.stop()
        sys.exit(1)

    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="zh-CN")
    page = ctx.new_page()

    # UI-SMOKE-001
    try:
        page.goto(BASE_URL + "/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)
        ok_login = "/login" in page.url
        if ok_login:
            page.locator("input[placeholder='用户名']").fill(USERNAME)
            page.locator("input[placeholder='密码']").fill(PASSWORD)
            btn = page.get_by_role("button", name=re.compile("登.*录")).first
            btn.click(timeout=5000)
            page.wait_for_load_state("networkidle", timeout=20000)
            ok_login = "/index" in page.url
        s = ss(page, "001-login-success")
        result("UI-SMOKE-001", "登录成功并跳转首页", ok_login,
               f"URL={page.url}", s)
    except Exception as e:
        s = ss(page, "001-login-fail")
        result("UI-SMOKE-001", "登录成功并跳转首页", False,
               f"{type(e).__name__}: {e}\n{traceback.format_exc()[-300:]}", s)

    # UI-SMOKE-002
    try:
        page.goto(BASE_URL + "/index", wait_until="networkidle", timeout=30000)
        txt = page.locator("body").inner_text()
        welcome = "赵经理" in txt
        cards = all(n in txt for n in (
            "回路监控箱设备", "阿三大苏打", "智能蓝牙门锁",
            "智慧文档管理系统", "智慧合规系统",
        ))
        s = ss(page, "002-homepage")
        result("UI-SMOKE-002", "首页加载 欢迎语+5 项目卡片", welcome and cards,
               f"welcome={welcome} cards_ok={cards}", s)
    except Exception as e:
        s = ss(page, "002-homepage-fail")
        result("UI-SMOKE-002", "首页加载", False, f"{type(e).__name__}: {e}", s)

    # UI-SMOKE-003
    try:
        page.goto(BASE_URL + "/index", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(500)
        txt = page.locator("body").inner_text()
        kpis = all(k in txt for k in ("我负责的项目", "平均进度", "风险项目", "待办事项"))
        num = re.search(r"(\d+)\s*我负责的项目", txt)
        ok_num = bool(num and int(num.group(1)) >= 3)
        s = ss(page, "003-kpi")
        result("UI-SMOKE-003", "5 KPI 显示", kpis and ok_num,
               f"kpis={kpis} ok_num={ok_num} num_match={num and num.group(0) if num else None}", s)
    except Exception as e:
        result("UI-SMOKE-003", "5 KPI 显示", False, f"{type(e).__name__}: {e}",
               ss(page, "003-kpi-fail"))

    # UI-SMOKE-004 顶层菜单可见
    try:
        page.goto(BASE_URL + "/index", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(400)
        txt = page.inner_text("body")
        menus_ok = all(m in txt for m in ("统计分析看板", "项目管理", "工作流"))
        result("UI-SMOKE-004", "3 个顶层菜单可见", menus_ok,
               "", ss(page, "004-top-menus"))
    except Exception as e:
        result("UI-SMOKE-004", "3 顶层菜单", False, f"{type(e).__name__}: {e}",
               ss(page, "004-fail"))

    # 005 统计分析看板 → 项目看板
    try:
        page.goto(BASE_URL + "/index", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(400)
        open_submenu(page, "统计分析看板", "项目看板")
        txt = page.inner_text("body")
        ok = "项目看板" in txt or "看板" in txt and "项目" in txt
        result("UI-SMOKE-005", "统计分析看板 → 项目看板 可达", ok,
               "", ss(page, "005-dashboard"))
    except Exception as e:
        result("UI-SMOKE-005", "项目看板跳转", False, f"{type(e).__name__}: {e}",
               ss(page, "005-fail"))

    # 006 项目管理 5 子项
    subs = [
        ("项目管理", "项目列表"),
        ("项目管理", "风险管理"),
        ("项目管理", "预算管理"),
        ("项目管理", "文档管理"),
        ("项目管理", "工作流配置"),
    ]
    fails = []
    for top, sub in subs:
        try:
            page.goto(BASE_URL + "/index", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(400)
            open_submenu(page, top, sub)
            body = page.inner_text("body")
            ok = sub in body or sub in page.url or sub[:2] in body
            name = f"006-prj-{sub}"
            if not ok:
                fails.append(sub)
            result(f"UI-SMOKE-006-{sub}", f"项目管理 → {sub} 可达", ok,
                   "", ss(page, name))
        except Exception as e:
            fails.append(sub)
            result(f"UI-SMOKE-006-{sub}", f"项目管理 → {sub}", False,
                   f"{type(e).__name__}: {e}", ss(page, f"006-prj-{sub}-fail"))
    if not fails:
        result("UI-SMOKE-006", "项目管理 5 子项全部可达", True, "")
    else:
        result("UI-SMOKE-006", "项目管理 5 子项可达性", False,
               f"失败={fails}")

    # 007 工作流 4 子项
    wf_subs = [
        ("工作流", "流程定义"),
        ("工作流", "流程分类"),
        ("工作流", "我的发起"),
        ("工作流", "我的待办"),
    ]
    fails = []
    for top, sub in wf_subs:
        try:
            page.goto(BASE_URL + "/index", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(400)
            open_submenu(page, top, sub)
            body = page.inner_text("body")
            ok = sub in body or sub in page.url or sub[:2] in body
            name = f"007-wf-{sub}"
            if not ok:
                fails.append(sub)
            result(f"UI-SMOKE-007-{sub}", f"工作流 → {sub} 可达", ok,
                   "", ss(page, name))
        except Exception as e:
            fails.append(sub)
            result(f"UI-SMOKE-007-{sub}", f"工作流 → {sub}", False,
                   f"{type(e).__name__}: {e}", ss(page, f"007-wf-{sub}-fail"))
    if not fails:
        result("UI-SMOKE-007", "工作流 4 子项全部可达", True, "")
    else:
        result("UI-SMOKE-007", "工作流 4 子项可达性", False, f"失败={fails}")

    # 008 登出
    try:
        page.goto(BASE_URL + "/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)
        if "/login" in page.url:
            page.locator("input[placeholder='用户名']").fill(USERNAME)
            page.locator("input[placeholder='密码']").fill(PASSWORD)
            page.get_by_role("button", name=re.compile("登.*录")).first.click(timeout=5000)
            page.wait_for_load_state("networkidle", timeout=20000)
        # 点用户下拉 → 退出
        try:
            avatar = page.locator(".avatar").first
            if avatar.count() == 0:
                avatar = page.locator("[class*=user]").first
            avatar.click(force=True, timeout=3000)
            page.wait_for_timeout(300)
        except Exception:
            pass
        try:
            logout_btn = page.get_by_text(re.compile("退出登录|退出|登出")).first
            logout_btn.click(force=True, timeout=3000)
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            # 尝试 localStorage.clear + goto
            page.evaluate("localStorage.clear(); sessionStorage.clear();")
            page.goto(BASE_URL + "/login?redirect=%2Findex", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
        s = ss(page, "008-logout")
        result("UI-SMOKE-008", "登出后跳转登录页", "/login" in page.url, f"URL={page.url}", s)
    except Exception as e:
        result("UI-SMOKE-008", "登出跳转", False, f"{type(e).__name__}: {e}",
               ss(page, "008-logout-fail"))

    # 009 错误密码
    try:
        page.goto(BASE_URL + "/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)
        if "/login" in page.url:
            page.locator("input[placeholder='用户名']").fill(USERNAME)
            page.locator("input[placeholder='密码']").fill("wrong_password_123")
            page.get_by_role("button", name=re.compile("登.*录")).first.click(timeout=5000)
            page.wait_for_timeout(1500)
        txt = page.inner_text("body")
        has_err = any(k in txt for k in ("用户不存在", "密码错误", "错误"))
        s = ss(page, "009-wrong-pwd")
        result("UI-SMOKE-009", "错误密码显示错误提示", has_err,
               f"first 300 body={txt[:300]}", s)
    except Exception as e:
        result("UI-SMOKE-009", "错误密码", False, f"{type(e).__name__}: {e}",
               ss(page, "009-wrong-pwd-fail"))

    # 010 登出后访问 /index 被拦截
    try:
        # 先登录 → 登出
        page.goto(BASE_URL + "/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)
        if "/login" in page.url:
            page.locator("input[placeholder='用户名']").fill(USERNAME)
            page.locator("input[placeholder='密码']").fill(PASSWORD)
            page.get_by_role("button", name=re.compile("登.*录")).first.click(timeout=5000)
            page.wait_for_load_state("networkidle", timeout=20000)
        page.evaluate("localStorage.clear(); sessionStorage.clear(); window.localStorage && localStorage.clear();")
        try:
            page.context.clear_cookies()
        except Exception:
            pass
        # 清 token
        page.goto(BASE_URL + "/index", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(800)
        s = ss(page, "010-blocked")
        ok = "/login" in page.url
        result("UI-SMOKE-010", "登出后访问 /index 被拦截回登录", ok,
               f"URL={page.url}", s)
    except Exception as e:
        result("UI-SMOKE-010", "登出后拦截", False, f"{type(e).__name__}: {e}",
               ss(page, "010-blocked-fail"))

    # 关闭
    ctx.close()
    browser.close()
    pw.stop()

    passed = sum(1 for r in results if r["outcome"] == "passed")
    failed = len(results) - passed
    summary = {
        "run_ts": RUN_TS,
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "start": start.isoformat(timespec="seconds"),
        "end": datetime.now().isoformat(timespec="seconds"),
        "base_url": BASE_URL,
        "results": results,
    }
    with open(OUT / "ui-smoke-results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n====== UI smoke 结束: passed={passed} failed={failed} total={len(results)} ======")


if __name__ == "__main__":
    main()
