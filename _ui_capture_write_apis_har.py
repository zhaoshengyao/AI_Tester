# -*- coding: utf-8 -*-
"""Step I-1：Playwright 自动化：赵老板账号登录 → 项目管理 → 尝试 7 个写操作按钮 → 录所有非 GET 请求
输出：
- projects/ipd/docs/analysis/zhaoboss-ui-write-captures/capture_manifest.json（所有捕获的非 GET 请求 + 每步截图路径 + 每页可见按钮文本）
- projects/ipd/docs/analysis/zhaoboss-ui-write-captures/*.png（每一步截图）
"""
from __future__ import annotations
import json, os, sys, time, uuid, re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

REPO = Path(r"d:\AICode\TestHub\AITestDemo")
OUT_DIR = REPO / "projects/ipd/docs/analysis/zhaoboss-ui-write-captures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST = OUT_DIR / "capture_manifest.json"

BASE_URL = "http://192.168.2.97:6090"
USERNAME = "赵老板"
PASSWORD = "123456"

captured_requests: list[dict] = []  # 所有非 GET 请求记录
step_logs: list[dict] = []  # 每步日志

def _safe_str(o, maxlen=2000):
    try:
        s = json.dumps(o, ensure_ascii=False)
    except Exception:
        s = str(o)
    if len(s) > maxlen: s = s[:maxlen] + "..."
    return s

def record_requests(page):
    """注册钩子：录【所有】非 GET 请求（req+resp）到 captured_requests（放宽 URL 过滤，避免漏抓）"""
    def _on_req(req):
        method = req.method.upper()
        if method == "GET": return
        url = req.url
        # 排除静态资源（.css .js .img .woff 等）和 websocket
        lower = url.lower()
        if any(x in lower for x in [".css", ".js", ".woff", ".ttf", ".eot", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", "websocket", "ws:", "wss:"]):
            return
        # 排除第三方（只保留 BASE_URL 或内网 192.168）
        if not (BASE_URL in url or "192.168." in url or "localhost" in lower or "/prod-api/" in lower or "/api/" in lower):
            return
        try:
            pd = req.post_data
            try:
                pd_json = json.loads(pd) if pd else None
            except Exception:
                pd_json = {"_raw": pd[:3000] if pd else None}
        except Exception:
            pd_json = None
        captured_requests.append({
            "ts": time.time(),
            "method": method,
            "url": url,
            "path_without_base": re.sub(r"^https?://[^/]+", "", url),
            "post_data": pd_json,
            "resource_type": req.resource_type,
            "headers_subset": {k: v for k, v in req.headers.items() if k.lower() in {"authorization","content-type","clientid","tenant-id"}},
            "response": None,  # 后面填
        })

    def _on_resp(resp):
        req = resp.request
        if req.method.upper() == "GET": return
        url = req.url
        lower = url.lower()
        if any(x in lower for x in [".css", ".js", ".woff", ".ttf", ".eot", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", "websocket", "ws:", "wss:"]):
            return
        if not (BASE_URL in url or "192.168." in url or "localhost" in lower or "/prod-api/" in lower or "/api/" in lower):
            return
        # 匹配最后一条同 url+method 未填 response 的
        for cr in reversed(captured_requests):
            if cr["response"] is None and cr["method"] == req.method.upper() and cr["url"] == url:
                try:
                    status = resp.status
                    try:
                        body = resp.json()
                    except Exception:
                        try: body = {"_raw_text": resp.text()[:1500]}
                        except Exception: body = None
                except Exception:
                    status = None; body = None
                cr["response"] = {"status": status, "body_sample": body}
                break

    page.on("request", _on_req)
    page.on("response", _on_resp)

def dump_buttons_and_links(page, step_name):
    """dump 当前页所有可见 button / a / .btn / el-button 等文本 + 选择器"""
    try:
        buttons = page.evaluate("""() => {
            const r = [];
            const tags = ['button','a','[role="button"]','.btn','.el-button','.ant-btn','span','div'];
            for (const sel of tags) {
                document.querySelectorAll(sel).forEach(el => {
                    if (!el.offsetParent) return; // 隐藏跳过
                    const t = (el.innerText || el.textContent || '').replace(/\\s+/g,' ').trim();
                    if (!t || t.length > 30) return;
                    let sel_str = el.tagName.toLowerCase();
                    if (el.id) sel_str += '#'+el.id;
                    if (el.className && typeof el.className === 'string') {
                        const c = el.className.trim().split(/\\s+/).filter(x => x.startsWith('el-') || x.startsWith('ant-') || x==='btn').join('.');
                        if (c) sel_str += '.'+c;
                    }
                    sel_str += ':text("'+t.replace(/"/g,'\\"')+'")';
                    r.push({text: t, selector: sel_str.substring(0, 200)});
                });
            }
            // 去重
            const seen = new Set(); const out = [];
            for (const b of r) { if (!seen.has(b.text)) { seen.add(b.text); out.push(b); } }
            return out.slice(0, 60);
        }""")
        return buttons
    except Exception as e:
        return [{"text": f"[ERROR dump buttons] {e}", "selector": ""}]

def log_step(step_id: str, step_title: str, page, ok: bool, note: str = ""):
    shot = OUT_DIR / f"step_{step_id}_{int(time.time())}.png"
    try:
        page.screenshot(path=str(shot), full_page=True)
        shot_rel = str(shot.relative_to(REPO))
    except Exception as e:
        shot_rel = ""
        note += f" [screenshot fail: {e}]"
    btns = dump_buttons_and_links(page, step_id)
    step_logs.append({
        "step_id": step_id, "step_title": step_title, "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ok": ok, "note": note,
        "screenshot": shot_rel,
        "current_url": page.url,
        "page_title": page.title(),
        "visible_buttons_links_top60": btns,
    })

def try_click_text(page, candidates: list[str]) -> tuple[bool, str, str]:
    """尝试按顺序点击文本匹配的按钮（中文全文匹配）。返回 (success, clicked_text, note)"""
    for txt in candidates:
        try:
            loc = page.get_by_text(txt, exact=True)
            if loc.count() > 0:
                first = loc.first
                first.click(timeout=8000)
                return True, txt, f"点击成功：{txt}"
        except Exception as e:
            # exact 失败 → 模糊 contains
            try:
                loc = page.get_by_text(txt)
                if loc.count() > 0:
                    first = loc.first
                    first.click(timeout=8000)
                    return True, txt, f"点击成功（模糊）：{txt}"
            except Exception as e2:
                continue
    # 最后：dump 所有按钮给用户判断
    btns = dump_buttons_and_links(page, "missing")
    return False, "", f"未找到候选按钮，当前页可见按钮前 60={json.dumps(btns, ensure_ascii=False)[:1500]}"

def try_fill_label(page, label_candidates: list[str], value: str) -> tuple[bool, str, str]:
    for lb in label_candidates:
        try:
            sel = page.get_by_label(lb)
            if sel.count(): sel.first.fill(value, timeout=3000); return True, lb, f"按 label={lb} 填充成功"
        except Exception: pass
    # 按 placeholder
    for lb in label_candidates:
        try:
            sel = page.get_by_placeholder(lb)
            if sel.count(): sel.first.fill(value, timeout=3000); return True, lb, f"按 placeholder={lb} 填充成功"
        except Exception: pass
    # 按 CSS input[type=text/password] 第 N 个
    for i, inp_selector in enumerate(["input[type='text']", "input[type='password']", "input"]):
        try:
            all_inp = page.locator(inp_selector)
            if all_inp.count() > 0:
                # 第 0 个=用户名，第 1 个=密码
                idx = 0 if ("用户" in label_candidates[0] or "账号" in label_candidates[0] or "姓名" in label_candidates[0]) else 1 if ("密码" in label_candidates[0]) else 0
                if all_inp.count() > idx:
                    all_inp.nth(idx).fill(value, timeout=3000)
                    return True, f"{inp_selector}[{idx}]", f"按 CSS index 填充成功"
        except Exception: pass
    return False, "", f"未找到 {label_candidates[0]} 输入框"

def _get_dialog_scope(page):
    """返回包含「确 定」或「取 消」按钮的弹框 scope（playwright locator）。找不到返回 page 本身。"""
    # 候选：el-dialog / ant-modal / role=dialog / class=el-dialog
    for label in ["确 定", "确定", "取 消", "取消"]:
        try:
            btn = page.get_by_text(label, exact=True)
            if btn.count() > 0:
                el = btn.first
                # 向上找 8 级父级，直到找到 el-dialog/带 role=dialog / 或最大层级 div
                candidate = el.evaluate_handle("""(el) => {
                    let n = el; let last = el;
                    for (let i = 0; i < 10 && n && n.parentElement; i++) {
                        n = n.parentElement;
                        const cls = (n.className || '').toString();
                        const role = n.getAttribute && n.getAttribute('role');
                        const tag = n.tagName ? n.tagName.toLowerCase() : '';
                        if (cls.includes('el-dialog') || cls.includes('ant-modal') || cls.includes('modal-body') || role === 'dialog' || tag === 'dialog') return n;
                        if (cls.includes('el-dialog__wrapper') || cls.includes('ant-modal-wrap')) return n;
                        last = n;
                    }
                    return last;
                }""")
                # candidate 是 ElementHandle → 转 Locator：用 xpath 方式（evaluate_handle 直接给节点就可转 locator？简化：直接用 CSS 取 .el-dialog:has-text(「确 定」)）
                # 上面 evaluate_handle 拿了真实 DOM，简化：直接定位 el-dialog 包含文本「确 定」的即可
                break
        except Exception: pass
    # 简化版：el-dialog 包含「取 消」或「确 定」的
    for css in [".el-dialog", ".ant-modal", ".el-message-box", ".modal", "[role='dialog']"]:
        try:
            all_dlg = page.locator(css)
            cnt = all_dlg.count()
            # 从后往前=最后一个弹框
            for i in range(cnt - 1, -1, -1):
                dlg = all_dlg.nth(i)
                try:
                    if dlg.is_visible(timeout=800):
                        for btn_t in ["确 定", "确定", "取 消", "取消"]:
                            try:
                                if dlg.get_by_text(btn_t, exact=True).count() > 0:
                                    return dlg
                            except Exception: pass
                except Exception: pass
        except Exception: pass
    return None

def _scope_fill_label(page, scope, label_candidates, value):
    """在弹框 scope 内 fill。scope=None 时退化到全局 fill"""
    target = scope or page
    for lb in label_candidates:
        try:
            sel = target.get_by_label(lb)
            if sel.count(): sel.first.fill(value, timeout=3000); return True, lb, f"scope 内 label={lb} 填充成功"
        except Exception: pass
    for lb in label_candidates:
        try:
            sel = target.get_by_placeholder(lb)
            if sel.count(): sel.first.fill(value, timeout=3000); return True, lb, f"scope 内 placeholder={lb} 填充成功"
        except Exception: pass
    # 弹框内 input 列表：按顺序=第 0=项目编号 1=项目名称 2=合同编号 3=预算 ... 但 label 在前
    return False, "", f"scope 内未找到 {label_candidates[0]} 输入框"

def _scope_click_text(page, scope, text_candidates):
    """scope 内按文本点击，优先 exact；返回 (ok, text, note)"""
    target = scope or page
    for txt in text_candidates:
        try:
            loc = target.get_by_text(txt, exact=True)
            if loc.count() > 0:
                loc.first.click(timeout=5000)
                return True, txt, f"scope 内点击成功：{txt}"
        except Exception:
            try:
                loc = target.get_by_text(txt)
                if loc.count() > 0:
                    loc.first.click(timeout=5000)
                    return True, txt, f"scope 内模糊点击成功：{txt}"
            except Exception: continue
    return False, "", f"scope 内未找到候选文本 {text_candidates[:4]}"

def _scope_select_dropdown(page, scope, label_or_trigger_candidates, option_text_candidates):
    """弹框内选下拉：先点触发器=label 对应 el-select 或「请选择」文本 → 展开后点 option；返回 (ok, note)"""
    target = scope or page
    # 1) 先找触发器=包含"请选择"、可见
    trigger_ok, trigger_txt, note_t = False, "", ""
    for tri in label_or_trigger_candidates:
        try:
            loc = target.locator(f":has-text('{tri}')").locator(".el-select, .el-select-dropdown, .ant-select, select").first
            if loc.count() > 0 and loc.is_visible(timeout=800):
                loc.click(timeout=4000)
                trigger_ok, trigger_txt = True, tri
                note_t = f"触发器点击成功={tri} 方式1"
                break
        except Exception: pass
    if not trigger_ok:
        trigger_ok, trigger_txt, note_t = _scope_click_text(page, target, label_or_trigger_candidates)
    # 2) 等 0.5s，展开后选 option（option 在 body 级 el-select-dropdown 内，不在 scope 里=所以这里用全局 page）
    if trigger_ok:
        time.sleep(0.8)
        # ============ 优先 exact option ============
        for opt in option_text_candidates:
            try:
                opt_loc = page.get_by_role("option", name=opt, exact=True)
                if opt_loc.count() > 0 and opt_loc.first.is_visible(timeout=1000):
                    opt_loc.first.click(timeout=3000); return True, f"{note_t} · 选 option={opt} exact"
            except Exception: pass
        for opt in option_text_candidates:
            try:
                opt_loc = page.locator(".el-select-dropdown__item, .ant-select-item-option, .el-cascader-node, .el-tree-node__label").filter(has_text=opt).first
                if opt_loc.count() > 0 and opt_loc.is_visible(timeout=1000):
                    opt_loc.click(timeout=3000); return True, f"{note_t} · 选 option={opt} CSS filter"
            except Exception: pass
        # ============ Fallback1：直接在下拉里输入 option 文本（远程搜索）→回车 ============
        try:
            # 聚焦在 trigger 的 input 上=直接 type
            for opt in option_text_candidates:
                try:
                    page.keyboard.type(opt); time.sleep(0.6)
                    # 弹出来选项 → 回车
                    page.keyboard.press("Enter"); time.sleep(0.3)
                    return True, f"{note_t} · 键盘输入 {opt}+Enter 远程搜索 fallback"
                except Exception: pass
        except Exception: pass
        # ============ Fallback2：键盘↓选第一个+回车 ============
        try:
            page.keyboard.press("ArrowDown"); time.sleep(0.2)
            page.keyboard.press("Enter"); time.sleep(0.3)
            return True, f"{note_t} · 键盘↓+Enter 选第一项 fallback"
        except Exception: pass
        # 点空白处关下拉
        try: page.mouse.click(10, 10)
        except Exception: pass
    return False, f"触发器={trigger_ok}:{trigger_txt}|{note_t}"

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        print(f"[FATAL] playwright 未安装: {e}")
        MANIFEST.write_text(json.dumps({"error": "playwright 未安装，执行 pip install playwright && playwright install chromium"}, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.exit(2)

    with sync_playwright() as pw:
        # 直接使用本机已装的 Chrome（C:\Program Files\Google\Chrome\Application\chrome.exe），无需下载 Playwright 自带 Chromium
        CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        EDGE_PATH   = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        import os as _os
        exe = CHROME_PATH if _os.path.exists(CHROME_PATH) else EDGE_PATH if _os.path.exists(EDGE_PATH) else None
        if not exe:
            MANIFEST.write_text(json.dumps({"error": "本机未找到 Chrome/Edge"}, ensure_ascii=False, indent=2), encoding="utf-8")
            sys.exit(3)
        print(f"[INFO] 使用系统浏览器：{exe}")
        try:
            browser = pw.chromium.launch(headless=True, executable_path=exe)
        except Exception as e1:
            print(f"[WARN] headless=True 失败={e1}，回退 headless=False（如无桌面环境将再次失败）")
            browser = pw.chromium.launch(headless=False, executable_path=exe)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="zh-CN")
        page = ctx.new_page()
        record_requests(page)  # 挂钩子

        # ========== Step 0：登录 ==========
        try:
            page.goto(BASE_URL, timeout=60000, wait_until="domcontentloaded")
            time.sleep(2)
            try: page.wait_for_load_state("networkidle", timeout=15000)
            except Exception: pass
            ok_u, txt_u, note_u = try_fill_label(page, ["用户名", "账号", "用户", "请输入用户名", "请输入登录账号"], USERNAME)
            ok_p, txt_p, note_p = try_fill_label(page, ["密码", "请输入密码", "登录密码"], PASSWORD)
            ok_l, txt_l, note_l = try_click_text(page, ["登录", "登 录", "Sign in", "Login", "立即登录"])
            try: page.wait_for_load_state("networkidle", timeout=15000)
            except Exception: pass
            time.sleep(3)
            log_step("00_login", f"登录账号 {USERNAME}", page, ok_u and ok_p and ok_l, f"{note_u} | {note_p} | {note_l}")
        except Exception as e:
            log_step("00_login", f"登录账号 {USERNAME} 异常", page, False, f"EXCEPTION: {e}")

        # ========== Step 1：导航到 项目管理 → 点「全部项目 →」进入列表页 ==========
        try:
            ok_n, txt_n, note_n = try_click_text(page, ["项目管理", "IPD项目", "我的项目", "项目列表", "项目中心"])
            try: page.wait_for_load_state("networkidle", timeout=15000)
            except Exception: pass
            time.sleep(3)
            # 首页有「全部项目 →」的链接，点进去才是项目列表页（那里才有新增/编辑/流转按钮）
            ok_all, txt_all, note_all = try_click_text(page, ["全部项目 →", "查看全部 →", "全部项目", "查看全部", "所有项目"])
            try: page.wait_for_load_state("networkidle", timeout=15000)
            except Exception: pass
            time.sleep(3)
            log_step("01_nav_pm", "导航到项目管理页 → 全部项目列表", page,
                     ok_n and ok_all,
                     f"点一级菜单={ok_n}:{txt_n}|{note_n} · 点全部项目→={ok_all}:{txt_all}|{note_all}")
        except Exception as e:
            log_step("01_nav_pm", "导航异常", page, False, f"EXCEPTION: {e}")

        # ========== Step 2：新增项目（CREATE）==========
        _ts = time.strftime('%Y%m%d%H%M%S')
        created_project_name = f"AUTO-HAR-{_ts}"
        created_project_no = f"AUTO-NO-{_ts}"
        try:
            ok_c, txt_c, note_c = try_click_text(page, ["新增项目", "创建项目", "新建项目", "+ 新增项目", "新增", "添加项目", "创建"])
            time.sleep(2)
            # 如果弹出来=填项目名
            ok_fn = ok_fc = ok_ptype = ok_leader = False
            txt_fn = txt_fc = note_fn = note_fc = note_ptype = note_leader = "(未打开弹框)"
            if ok_c:
                # ---------- 关键：获取弹框 scope，所有 fill/click 都在弹框内做 ----------
                scope = _get_dialog_scope(page)
                note_scope = f"弹框scope={'找到' if scope is not None else '未找到,降级全局'}"
                # ---------- scope 内填：项目编号 ----------
                ok_fc, txt_fc, note_fc = _scope_fill_label(page, scope,
                    ["项目编号", "编号", "项目编码", "请输入项目编号"], created_project_no)
                # ---------- scope 内填：项目名称 ----------
                ok_fn, txt_fn, note_fn = _scope_fill_label(page, scope,
                    ["项目名称", "项目名", "名称", "请输入项目名称"], created_project_name)
                # ---------- scope 内下拉选：项目类型（必填=项目类型不能为空，默认软件研发） ----------
                ok_ptype, note_ptype = _scope_select_dropdown(page, scope,
                    ["项目类型", "类型", "请选择 项目类型", "请选择"],
                    ["软件研发", "硬件研发", "工程项目", "软件项目", "硬件项目"])
                # ---------- scope 内下拉选：项目状态（必填=请选择状态，默认草稿） ----------
                ok_pstatus, note_pstatus = _scope_select_dropdown(page, scope,
                    ["项目状态", "状态", "请选择状态"],
                    ["草稿", "待审批", "已立项"])
                # ---------- scope 内下拉选：项目负责人（必填=负责人不能为空，暴力：选第一个 option + 失败则连点2次 确认） ----------
                ok_leader, note_leader = _scope_select_dropdown(page, scope,
                    ["项目负责人", "负责人", "请选择负责人", "请选择"],
                    ["赵老板", "赵经理"])
                # ---------- 暴力兜底：如果负责人/状态/类型仍为空 → 直接点所有 .el-select → 每个 ↓+Enter ----------
                def _brute_select_all_in_dialog():
                    try:
                        sc = scope or page
                        selects = sc.locator(".el-select, .ant-select, select")
                        cnt = selects.count()
                        notes = []
                        for i in range(cnt):
                            try:
                                sel = selects.nth(i)
                                if sel.is_visible(timeout=500):
                                    sel.click(timeout=2000); time.sleep(0.5)
                                    try: page.keyboard.press("ArrowDown"); time.sleep(0.2); page.keyboard.press("Enter"); time.sleep(0.2)
                                    except Exception: pass
                                    notes.append(f"select[{i}] → ↓+Enter OK")
                            except Exception as ee:
                                notes.append(f"select[{i}] → fail")
                        return True, "暴力fill %d 个下拉: %s" % (cnt, "; ".join(notes[:10]))
                    except Exception as ee:
                        return False, f"暴力select失败={ee}"
                if not (ok_ptype and ok_pstatus and ok_leader):
                    ok_b, note_b = _brute_select_all_in_dialog()
                    if not ok_ptype: ok_ptype, note_ptype = ok_b, f"(暴力兜底后) {note_b}"
                    if not ok_pstatus: ok_pstatus, note_pstatus = ok_b, f"(暴力兜底后) {note_b}"
                    if not ok_leader: ok_leader, note_leader = ok_b, f"(暴力兜底后) {note_b}"
                # ---------- 点确定/保存（弹框内） ----------
                ok_s, txt_s, note_s = _scope_click_text(page, scope, ["确 定", "确定", "保存", "提交", "创建", "立即创建"])
                if not ok_s:
                    # 弹框没找到=回退全局
                    ok_s, txt_s, note_s = try_click_text(page, ["确 定", "确定", "保存", "提交", "创建"])
                time.sleep(1.2)
                # ---------- 关键：如果弹框还在（确 定 仍可见=前端校验拦住=还有其他必填） ----------
                # 再尝试 scope 内填 开始日期+结束日期（ElementUI datepicker 一般靠 label 选）
                def _still_has_ok_dialog():
                    try:
                        return (_get_dialog_scope(page) is not None)
                    except Exception: return False
                ok_s2, ok_sd, ok_ed = False, False, False
                note_sd = note_ed = "(未补填日期)"
                if _still_has_ok_dialog():
                    # scope 刷新一下（再找弹框）
                    scope = _get_dialog_scope(page)
                    ok_sd, _, note_sd = _scope_fill_label(page, scope,
                        ["开始日期", "计划开始日期", "起始日期", "startDate"], "2026-08-12")
                    ok_ed, _, note_ed = _scope_fill_label(page, scope,
                        ["结束日期", "计划结束日期", "完成日期", "endDate"], "2026-12-31")
                    # 再次点确 定
                    ok_s2, txt_s2, note_s2 = _scope_click_text(page, scope, ["确 定", "确定", "保存", "提交"])
                    if ok_s2:
                        ok_s, txt_s, note_s = True, txt_s2, f"{note_s} · 补填日期后再确定={note_s2}"
                    else:
                        note_s += f" · 补填开始日期={ok_sd}|{note_sd} 结束日期={ok_ed}|{note_ed} · 再确定失败={note_s2}"
                # ========== 关键：第三次=若弹框仍在 → dump 所有「不能为空/必填/请选择」错误提示文字 ==========
                _error_txt = "(无)"
                if _still_has_ok_dialog():
                    try:
                        _error_txt = page.evaluate("""() => {
                            const out = [];
                            const sel = document.querySelectorAll('.el-form-item__error, .el-message__content, .ant-form-item-explain-error, .el-form-item__content, [class*="error"], .el-message, .el-notification__content');
                            sel.forEach(e => {
                                const t = (e.innerText || e.textContent || '').replace(/\\s+/g,' ').trim();
                                if (t && (t.includes('不能') || t.includes('必填') || t.includes('请选择') || t.includes('请输入') || t.includes('为空') || t.includes('失败') || t.includes('错误'))) out.push(t.substring(0, 120));
                            });
                            // 再全页扫一遍
                            document.body.innerText.split(/\\n+/).forEach(ln => {
                                const t = ln.trim();
                                if (t && (t.includes('不能为空') || t.includes('必填') || t.includes('错误') || t.includes('失败'))) out.push(t.substring(0, 120));
                            });
                            return [...new Set(out)].slice(0, 20).join(' | ');
                        }""") or "(无)"
                    except Exception as ee:
                        _error_txt = f"[dump errors fail] {ee}"
                try: page.wait_for_load_state("networkidle", timeout=20000)
                except Exception: pass
                time.sleep(3)
            else:
                ok_s = False; txt_s = "未打开新增弹框"; note_s = note_c
                note_scope = "未打开新增弹框"
            log_step("02_create_project", f"新增项目：{created_project_name}", page,
                     ok_c and ok_fn and ok_fc and ok_ptype and ok_pstatus and ok_leader and ok_s,
                     f"scope={note_scope} · 点新增={ok_c}:{txt_c}|{note_c} · "
                     f"填编号={ok_fc}:{txt_fc}|{note_fc} · 填项目名={ok_fn}:{txt_fn}|{note_fn} · "
                     f"选项目类型={ok_ptype}|{note_ptype} · 选项目状态={ok_pstatus}|{note_pstatus} · "
                     f"选负责人={ok_leader}|{note_leader} · "
                     f"保存确定={ok_s}:{txt_s}|{note_s} · "
                     f"【表单错误提示】: {_error_txt}")
        except Exception as e:
            log_step("02_create_project", "新增异常", page, False, f"EXCEPTION: {e}")

        # ========== Step 2.b：找到刚创建的 AUTO-HAR 项目 → 点「查看」进入详情页（详情页里才有提交审批/推进阶段按钮）==========
        def _find_and_enter_detail(page, project_name: str, step_title: str) -> tuple[bool, str]:
            """在列表页搜索项目名 → 点行内「查看」或点项目名链接，进入详情页。
            关键点：先点「重置」清空所有默认筛选，避免被筛选条件过滤掉新项目。"""
            try:
                # 1) 先清空所有筛选条件
                try_click_text(page, ["重置"])
                time.sleep(1.5)
                try: page.wait_for_load_state("networkidle", timeout=8000)
                except Exception: pass
                # 2) 搜索框=项目名称（dump 里看到的 label="项目名称"）
                ok_s, txt_s, note_s = try_fill_label(page, ["搜索", "请输入项目名称", "项目名称搜索", "项目名称", "关键字"], project_name)
                if ok_s:
                    try:
                        ok_go, _, _ = try_click_text(page, ["筛选", "查询", "搜索", "查 询"])  # 点筛选按钮
                        if not ok_go: page.keyboard.press("Enter")
                    except Exception: page.keyboard.press("Enter")
                    time.sleep(2.5)
                    try: page.wait_for_load_state("networkidle", timeout=12000)
                    except Exception: pass
                # 3) 优先点项目名链接（a.el-link）=点详情
                ok_detail, txt_detail, note_detail = try_click_text(page, [project_name])
                if not ok_detail:
                    # 没匹配到项目名=可能是刚创建没刷新=直接点列表第一行的 查看/项目名链接（第 1 行）
                    try:
                        first_row_view = page.locator("button.el-button").filter(has_text="查看").first
                        if first_row_view.count() > 0 and first_row_view.is_visible(timeout=1000):
                            first_row_view.click(timeout=4000)
                            ok_detail, txt_detail, note_detail = True, "第一行查看按钮", "点列表第一行查看按钮 fallback"
                    except Exception as ee:
                        if not ok_detail:
                            # 最后一招：点第一个 a.el-link 链接（项目名）
                            try:
                                first_proj_link = page.locator("a.el-link").first
                                if first_proj_link.count() > 0 and first_proj_link.is_visible(timeout=1000):
                                    first_proj_link.click(timeout=4000)
                                    ok_detail, txt_detail, note_detail = True, "第一个 a.el-link", f"fallback 点击第一个项目名链接 fallback {ee}"
                            except Exception: pass
                try: page.wait_for_load_state("networkidle", timeout=15000)
                except Exception: pass
                time.sleep(3)
                return ok_detail, f"重置筛选=True · 搜索={ok_s}:{txt_s}|{note_s} · 进详情={ok_detail}:{txt_detail}|{note_detail}"
            except Exception as e:
                return False, f"EXCEPTION: {e}"

        # ========== Step 3：详情页内提交审批（draft→pending）==========
        try:
            ok_detail, note_detail = _find_and_enter_detail(page, created_project_name, "submit detail")
            # 详情页流转按钮常见：发起立项申请(draft→pending) / 送审 / 发起审批 等
            ok_sub, txt_sub, note_sub = try_click_text(page, [
                "发起立项申请", "提交审批", "送审", "审批提交", "发起审批", "提交审核", "提交立项申请",
                "立项申请提交", "发起立项", "启动立项",
            ])
            if ok_sub:
                # 可能有弹框=填审批意见+确定/确 定
                try_fill_label(page, ["审批意见", "意见", "备注", "说明"], "WR 自动测试提交=赵老板")
                ok_ok, txt_ok, note_ok = try_click_text(page, ["确 定", "确定", "确认", "提交", "发起"])
                if not ok_ok:
                    try: page.keyboard.press("Enter")
                    except Exception: pass
                try: page.wait_for_load_state("networkidle", timeout=20000)
                except Exception: pass
                note_sub += f" | 弹框确认={ok_ok}:{txt_ok}|{note_ok}"
            # 无论 ok_sub 成功与否，dump 当前页所有按钮文本=供下一轮修
            log_step("03_submit_approval", f"草稿→提交审批 pending（{created_project_name}）", page,
                     ok_detail and ok_sub, f"进详情={note_detail} · 提交={ok_sub}:{txt_sub}|{note_sub}")
            # 回列表页
            try:
                try_click_text(page, ["项目列表", "返回列表", "返 回", "返回"])
                time.sleep(2)
            except Exception: pass
        except Exception as e:
            log_step("03_submit_approval", "提交审批异常", page, False, f"EXCEPTION: {e}")

        # ========== Step 4：审批通过（pending→approved）==========
        try:
            try:
                try_click_text(page, ["项目列表", "返回列表", "返 回", "返回"])
                time.sleep(2); page.wait_for_load_state("networkidle", timeout=10000)
            except Exception: pass
            ok_detail, note_detail = _find_and_enter_detail(page, created_project_name, "approve detail")
            ok_a, txt_a, note_a = try_click_text(page, [
                "审批通过", "通过", "同意", "批准", "审批", "审核通过", "立项", "立项通过",
            ])
            if ok_a:
                try_fill_label(page, ["审批意见", "意见"], "WR 自动测试=赵老板审批通过")
                ok_ok, txt_ok, note_ok = try_click_text(page, ["确 定", "确定", "确认", "通过"])
                if not ok_ok:
                    try: page.keyboard.press("Enter")
                    except Exception: pass
                try: page.wait_for_load_state("networkidle", timeout=20000)
                except Exception: pass
                note_a += f" | 弹框确认={ok_ok}:{txt_ok}|{note_ok}"
            log_step("04_approve", f"待审批→审批通过 approved（{created_project_name}）", page,
                     ok_detail and ok_a, f"进详情={note_detail} · 审批={ok_a}:{txt_a}|{note_a}")
        except Exception as e:
            log_step("04_approve", "审批异常", page, False, f"EXCEPTION: {e}")

        # ========== Step 5：phase concept→plan ==========
        try:
            try:
                try_click_text(page, ["项目列表", "返回列表", "返 回", "返回"])
                time.sleep(2); page.wait_for_load_state("networkidle", timeout=10000)
            except Exception: pass
            ok_detail, note_detail = _find_and_enter_detail(page, created_project_name, "concept→plan")
            ok_adv, txt_adv, note_adv = try_click_text(page, [
                "推进阶段", "下一阶段", "进入下一阶段", "立项", "启动计划阶段", "阶段推进", "启动立项", "进入计划",
            ])
            if ok_adv:
                ok_ok, txt_ok, note_ok = try_click_text(page, ["确 定", "确定", "确认", "进入", "推进"])
                if not ok_ok:
                    try: page.keyboard.press("Enter")
                    except Exception: pass
                try: page.wait_for_load_state("networkidle", timeout=20000)
                except Exception: pass
                note_adv += f" | 弹框确认={ok_ok}:{txt_ok}|{note_ok}"
            log_step("05_phase_concept_plan", f"phase concept→plan（{created_project_name}）", page,
                     ok_detail and ok_adv, f"进详情={note_detail} · 推进={ok_adv}:{txt_adv}|{note_adv}")
        except Exception as e:
            log_step("05_phase_concept_plan", "phase 推进异常", page, False, f"EXCEPTION: {e}")

        # ========== Step 6：phase plan→development ==========
        try:
            try:
                try_click_text(page, ["项目列表", "返回列表", "返 回", "返回"])
                time.sleep(2); page.wait_for_load_state("networkidle", timeout=10000)
            except Exception: pass
            ok_detail, note_detail = _find_and_enter_detail(page, created_project_name, "plan→dev")
            ok_adv, txt_adv, note_adv = try_click_text(page, [
                "推进阶段", "下一阶段", "开始开发", "进入开发阶段", "开发启动", "启动开发",
            ])
            if ok_adv:
                ok_ok, txt_ok, note_ok = try_click_text(page, ["确 定", "确定", "确认", "进入", "推进"])
                if not ok_ok:
                    try: page.keyboard.press("Enter")
                    except Exception: pass
                try: page.wait_for_load_state("networkidle", timeout=20000)
                except Exception: pass
                note_adv += f" | 弹框确认={ok_ok}:{txt_ok}|{note_ok}"
            log_step("06_phase_plan_dev", f"phase plan→development（{created_project_name}）", page,
                     ok_detail and ok_adv, f"进详情={note_detail} · 推进={ok_adv}:{txt_adv}|{note_adv}")
        except Exception as e:
            log_step("06_phase_plan_dev", "phase 推进异常", page, False, f"EXCEPTION: {e}")

        # ========== Step 7：phase development→closed ==========
        try:
            try:
                try_click_text(page, ["项目列表", "返回列表", "返 回", "返回"])
                time.sleep(2); page.wait_for_load_state("networkidle", timeout=10000)
            except Exception: pass
            ok_detail, note_detail = _find_and_enter_detail(page, created_project_name, "dev→closed")
            ok_adv, txt_adv, note_adv = try_click_text(page, [
                "结项", "关闭项目", "完成", "推进阶段", "下一阶段", "项目完成", "验收结项", "项目结项",
            ])
            if ok_adv:
                ok_ok, txt_ok, note_ok = try_click_text(page, ["确 定", "确定", "确认", "结项"])
                if not ok_ok:
                    try: page.keyboard.press("Enter")
                    except Exception: pass
                try: page.wait_for_load_state("networkidle", timeout=20000)
                except Exception: pass
                note_adv += f" | 弹框确认={ok_ok}:{txt_ok}|{note_ok}"
            log_step("07_phase_dev_closed", f"phase development→closed（{created_project_name}）", page,
                     ok_detail and ok_adv, f"进详情={note_detail} · 结项={ok_adv}:{txt_adv}|{note_adv}")
        except Exception as e:
            log_step("07_phase_dev_closed", "结项异常", page, False, f"EXCEPTION: {e}")

        # ========== Step 8：软删除（避免数据污染，用刚创建的专用项目）==========
        try:
            try:
                try_click_text(page, ["项目列表", "返回列表", "返 回", "返回"])
                time.sleep(2); page.wait_for_load_state("networkidle", timeout=10000)
            except Exception: pass
            ok_detail, note_detail = _find_and_enter_detail(page, created_project_name, "soft-delete")
            # 详情页通常有「删除/归档/回收」按钮；没有就回列表操作列表上的删除
            ok_d, txt_d, note_d = try_click_text(page, [
                "删除", "移除", "软删除", "移到回收站", "回收", "归档", "废弃", "解散项目", "删除项目",
            ])
            if not ok_d:
                # 回列表，点第一行删除按钮
                try:
                    try_click_text(page, ["项目列表", "返回列表"])
                    time.sleep(2)
                    # 搜索项目
                    try_click_text(page, ["重置"])
                    time.sleep(1)
                    ok_s, _, _ = try_fill_label(page, ["搜索", "请输入项目名称"], created_project_name)
                    if ok_s:
                        try: page.keyboard.press("Enter"); time.sleep(2)
                        except Exception: pass
                    ok_d, txt_d, note_d = try_click_text(page, ["删除", "移到回收站"])
                except Exception: pass
            if ok_d:
                ok_ok, txt_ok, note_ok = try_click_text(page, ["确 定", "确定", "确认", "删除", "移到回收站"])
                if not ok_ok:
                    try: page.keyboard.press("Enter")
                    except Exception: pass
                try: page.wait_for_load_state("networkidle", timeout=20000)
                except Exception: pass
                note_d += f" | 弹框确认={ok_ok}:{txt_ok}|{note_ok}"
            log_step("08_soft_delete", f"删除/归档/回收专用项目（{created_project_name}）", page,
                     ok_detail and ok_d, f"进详情={note_detail} · 删除={ok_d}:{txt_d}|{note_d}")
        except Exception as e:
            log_step("08_soft_delete", "删除异常", page, False, f"EXCEPTION: {e}")

        # ========== 收尾：存 manifest ==========
        manifest = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": BASE_URL,
            "username": USERNAME,
            "created_project_name_candidate": created_project_name,
            "captured_non_get_requests": captured_requests,
            "step_logs": step_logs,
            "summary": {
                "total_non_get_captured": len(captured_requests),
                "success_code200": sum(1 for x in captured_requests if isinstance(x.get("response"), dict) and x["response"].get("status") == 200 and isinstance(x["response"].get("body_sample"), dict) and x["response"]["body_sample"].get("code") == 200),
                "step_success_count": sum(1 for x in step_logs if x["ok"]),
                "step_total": len(step_logs),
            }
        }
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] 捕获清单 → {MANIFEST}")
        print(f"   - 非 GET 请求：{len(captured_requests)}（HTTP200+code200 = {manifest['summary']['success_code200']}）")
        print(f"   - 步骤成功：{manifest['summary']['step_success_count']}/{len(step_logs)}")
        for r in captured_requests:
            path = r["path_without_base"]
            method = r["method"]
            pd = r.get("post_data")
            resp = r.get("response") or {}
            st = resp.get("status")
            body = resp.get("body_sample") or {}
            biz = body.get("code") if isinstance(body, dict) else None
            msg = (body.get("msg") or "") if isinstance(body, dict) else ""
            print(f"     {method:6s} {path[:120]:120s} HTTP={st} code={biz} msg={str(msg)[:60]}")
        browser.close()

if __name__ == "__main__":
    main()
