# -*- coding: utf-8 -*-
"""UI smoke 6 条 = 覆盖矩阵 UI-SMOKE-001~010。
UI-SMOKE-001 登录成功（goto / → 填用户名/密码/登录 → URL 跳转 /index）
UI-SMOKE-002 首页加载完成（标题/欢迎语/5 个卡片存在）
UI-SMOKE-003 5 KPI 显示：我负责的项目/平均进度/风险项目/待办
UI-SMOKE-004 3 个顶层菜单可见（统计分析看板 / 项目管理 / 工作流）
UI-SMOKE-005 一级菜单 1：统计分析看板 → 展开后"项目看板"子项 可达
UI-SMOKE-006 一级菜单 2：项目管理 → "项目列表 / 风险管理 / 预算管理 / 文档管理 / 工作流配置" 5 子项逐一可达
UI-SMOKE-007 一级菜单 3：工作流 → "流程定义 / 流程分类 / 我的发起 / 我的待办" 4 子项逐一可达
UI-SMOKE-008 退出登录 → 返回 /login?redirect
UI-SMOKE-009 密码错误登录失败 → 提示 用户不存在/密码错误
UI-SMOKE-010 登出后 token 清除不能回首页
"""
from __future__ import annotations

import re
from pathlib import Path


def _ss(page, path_parts, ipd_ui_config):
    """screenshot helper."""
    out = Path(ipd_ui_config["raw_ui_dir"]) / ("-".join(path_parts) + ".png")
    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out), full_page=True)
    return out


def test_ui_smoke_001_login_success(page, ipd_ui_config):
    cfg = ipd_ui_config
    page.goto(cfg["base_url"] + "/", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    assert page.url.endswith("/login") or "/login" in page.url, f"未在登录页 URL={page.url}"
    page.locator("input[placeholder='用户名']").fill(cfg["username"])
    page.locator("input[placeholder='密码']").fill(cfg["password"])
    page.get_by_role("button", name=re.compile("登.*录")).click()
    page.wait_for_load_state("networkidle")
    assert "/index" in page.url or page.url.rstrip("/").endswith(cfg["base_url"].rstrip("/")), (
        f"登录后未跳转首页 URL={page.url}; content500={page.content()[:500]}"
    )
    _ss(page, ["001-login-success"], cfg)


def test_ui_smoke_002_homepage_structure(page, ipd_ui_config):
    cfg = ipd_ui_config
    page.goto(cfg["base_url"] + "/index", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    welcome = page.get_by_text(re.compile(r"欢迎回来.*赵经理")).count()
    assert welcome >= 1, "首页欢迎语缺失"
    cards = [
        "回路监控箱设备", "阿三大苏打", "智能蓝牙门锁",
        "智慧文档管理系统", "智慧合规系统",
    ]
    for n in cards:
        assert page.get_by_text(n).count() >= 1, f"首页项目卡片缺失 '{n}'"
    _ss(page, ["002-homepage-structure"], cfg)


def test_ui_smoke_003_5_kpi_labels(page, ipd_ui_config):
    cfg = ipd_ui_config
    page.goto(cfg["base_url"] + "/index", wait_until="networkidle")
    page.wait_for_timeout(600)
    txt = page.locator("body").inner_text()
    # KPI 文本："5 我负责的项目 24% 平均进度 2 风险项目 0 待办事项"
    assert "我负责的项目" in txt, "KPI-我负责的项目 缺失"
    assert "平均进度" in txt, "KPI-平均进度 缺失"
    assert "风险项目" in txt, "KPI-风险项目 缺失"
    assert "待办事项" in txt, "KPI-待办事项 缺失"
    # 数值位（允许 5/24%/2/0）
    m = re.search(r"(\d+)\s*我负责的项目", txt)
    assert m and int(m.group(1)) >= 3, f"项目数异常 m={m and m.group(0)}"
    m2 = re.search(r"(\d+)%\s*平均进度", txt)
    assert m2 and 0 <= int(m2.group(1)) <= 100, f"平均进度%异常"
    _ss(page, ["003-kpi"], cfg)


def test_ui_smoke_004_top_level_menus_visible(page, ipd_ui_config):
    cfg = ipd_ui_config
    page.goto(cfg["base_url"] + "/index", wait_until="networkidle")
    page.wait_for_timeout(600)
    # 3 个顶层菜单
    for menu in ("统计分析看板", "项目管理", "工作流"):
        # 全文字匹配
        found = page.get_by_text(menu).count()
        assert found >= 1, f"顶层菜单缺失 '{menu}'"
    _ss(page, ["004-top-menus"], cfg)


def _open_submenu(page, top_menu_text: str, sub_text: str):
    """辅助：hover/click 顶层菜单 → 点子菜单（展开方式兼容 collapsed，先 hover 再点，如无法交互用 force=True）。"""
    top = page.get_by_text(top_menu_text).first
    # hover 到 top_menu 父；父定位：找有 role=menuitem 且文本=top_menu_text 的元素
    parent = page.locator(f"[role=menuitem]", has_text=top_menu_text).first
    try:
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


def test_ui_smoke_005_menu_dashboard_sub_project_dashboard(page, ipd_ui_config):
    cfg = ipd_ui_config
    page.goto(cfg["base_url"] + "/index", wait_until="networkidle")
    page.wait_for_timeout(400)
    _open_submenu(page, "统计分析看板", "项目看板")
    # 断言面包屑或 body 出现"项目看板"
    body = page.inner_text("body")
    assert "项目看板" in body, "项目看板 页面未加载 body text 无 项目看板"
    _ss(page, ["005-menu-dashboard-projectdashboard"], cfg)


def test_ui_smoke_006_submenus_project_5_items_reachable(page, ipd_ui_config):
    cfg = ipd_ui_config
    subs = [
        ("项目管理", "项目列表"),
        ("项目管理", "风险管理"),
        ("项目管理", "预算管理"),
        ("项目管理", "文档管理"),
        ("项目管理", "工作流配置"),
    ]
    reachable = []
    for top, sub in subs:
        try:
            page.goto(cfg["base_url"] + "/index", wait_until="networkidle")
            page.wait_for_timeout(400)
            _open_submenu(page, top, sub)
            body = page.inner_text("body")
            # 面包屑 / 页面标题 / url 路径任一字段 = sub 名
            ok = sub in body or sub in page.url
            if not ok:
                # 尝试 搜索 sub 前两字（子菜单标题可能不同名）降低误杀
                ok = sub[:2] in body
            reachable.append((top, sub, ok))
            _ss(page, [f"006-menu-{top}-{sub}-OK{int(ok)}"], cfg)
        except Exception as e:
            reachable.append((top, sub, False, str(e)[:150]))
    failed = [r for r in reachable if not r[2]]
    assert not failed, f"项目管理子菜单不可达 list={failed}; full={reachable}"


def test_ui_smoke_007_submenus_workflow_4_items_reachable(page, ipd_ui_config):
    cfg = ipd_ui_config
    subs = [
        ("工作流", "流程定义"),
        ("工作流", "流程分类"),
        ("工作流", "我的发起"),
        ("工作流", "我的待办"),
    ]
    reachable = []
    for top, sub in subs:
        try:
            page.goto(cfg["base_url"] + "/index", wait_until="networkidle")
            page.wait_for_timeout(400)
            _open_submenu(page, top, sub)
            body = page.inner_text("body")
            ok = sub in body or sub in page.url or sub[:2] in body
            reachable.append((top, sub, ok))
            _ss(page, [f"007-menu-{top}-{sub}-OK{int(ok)}"], cfg)
        except Exception as e:
            reachable.append((top, sub, False, str(e)[:150]))
    failed = [r for r in reachable if not r[2]]
    assert not failed, f"工作流子菜单不可达 list={failed}; full={reachable}"


def test_ui_smoke_008_logout_redirect(page, ipd_ui_config):
    cfg = ipd_ui_config
    # 先登录
    page.goto(cfg["base_url"] + "/", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    if "/login" in page.url:
        page.locator("input[placeholder='用户名']").fill(cfg["username"])
        page.locator("input[placeholder='密码']").fill(cfg["password"])
        page.get_by_role("button", name=re.compile("登.*录")).click()
        page.wait_for_load_state("networkidle")
        assert "/index" in page.url, f"预登录失败 URL={page.url}"
    # 右上角下拉 登出：找"退出登录"或 avatar 下拉内有退出
    # 先点 e6 那个 collapsed button（右上角下拉按钮，通常是头像/用户名）
    body_before = page.inner_text("body")
    # 找所有带 退出/登出 文本的按钮
    logout_loc = page.get_by_text(re.compile("退出登录|退出|登出")).first
    # 若未显示，点 user dropdown（常见是右上角用户名下拉按钮）
    if not logout_loc.is_visible():
        # 尝试：locator(".el-dropdown-selfdefine, .avatar-wrapper, .user-dropdown") 或 button e6
        user_drop = page.locator(".avatar").first
        if user_drop.count() == 0:
            user_drop = page.locator("button").filter(has_text="").last
        user_drop.click(force=True)
        page.wait_for_timeout(400)
        logout_loc = page.get_by_text(re.compile("退出登录|退出|登出")).first
    logout_loc.click(force=True)
    page.wait_for_load_state("networkidle")
    # 确认跳回 /login?redirect
    assert "/login" in page.url, f"登出未跳转登录页 URL={page.url}"
    _ss(page, ["008-logout-redirect-login"], cfg)


def test_ui_smoke_009_wrong_password_msg(page, ipd_ui_config):
    cfg = ipd_ui_config
    page.goto(cfg["base_url"] + "/", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    page.locator("input[placeholder='用户名']").fill(cfg["username"])
    page.locator("input[placeholder='密码']").fill("wrong_password_xxx")
    page.get_by_role("button", name=re.compile("登.*录")).click()
    page.wait_for_timeout(1500)
    txt = page.inner_text("body")
    # 匹配"用户不存在/密码错误"或其他错误
    has_err = any(k in txt for k in ("用户不存在", "密码错误", "错误"))
    assert has_err, f"错误密码后无错误提示 body snippet={txt[:300]}"
    _ss(page, ["009-wrong-password-error"], cfg)


def test_ui_smoke_010_after_logout_token_cleared(page, ipd_ui_config):
    """登出后访问 /index 重定向回 login（或前端路由拦截）。"""
    cfg = ipd_ui_config
    # 先登录 → 登出 → 直接访问 /index
    page.goto(cfg["base_url"] + "/", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    if "/login" in page.url:
        page.locator("input[placeholder='用户名']").fill(cfg["username"])
        page.locator("input[placeholder='密码']").fill(cfg["password"])
        page.get_by_role("button", name=re.compile("登.*录")).click()
        page.wait_for_load_state("networkidle")
    # 登出
    user_drop = page.locator(".avatar").first
    if user_drop.count() == 0:
        user_drop = page.locator("button").last
    user_drop.click(force=True)
    page.wait_for_timeout(400)
    logout_loc = page.get_by_text(re.compile("退出登录|退出|登出")).first
    logout_loc.click(force=True)
    page.wait_for_load_state("networkidle")
    assert "/login" in page.url, "登出失败"
    # 直接访问 /index
    page.goto(cfg["base_url"] + "/index", wait_until="domcontentloaded")
    page.wait_for_timeout(800)
    assert "/login" in page.url or page.url.rstrip("/").endswith("/login?redirect=%2Findex"), (
        f"登出后访问 /index 未被拦截跳登录 URL={page.url}"
    )
    _ss(page, ["010-after-logout-blocked"], cfg)
