# -*- coding: utf-8 -*-
"""P0-2：Playwright 录编辑按钮请求 URL
1. 赵老板登录
2. 项目列表→进一个 approved 项目详情页
3. dump 详情页所有可见按钮
4. 点编辑→修改项目名→保存
5. 录网络请求（POST/PUT/PATCH）
"""
from __future__ import annotations
import json, os, sys, time, re
from pathlib import Path

REPO = Path(r"d:\AICode\TestHub\AITestDemo")
OUT_DIR = REPO / "projects/ipd/docs/analysis/zhaoboss-ui-write-captures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST = OUT_DIR / "edit_capture_manifest.json"

BASE_URL = "http://192.168.2.97:6090"
USERNAME = "赵老板"
PASSWORD = "123456"

captured_requests: list[dict] = []

def record_requests(page):
    def _on_req(req):
        method = req.method.upper()
        if method == "GET": return
        url = req.url
        lower = url.lower()
        if any(x in lower for x in [".css", ".js", ".woff", ".ttf", ".eot", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", "websocket", "ws:", "wss:"]):
            return
        if not (BASE_URL in url or "192.168." in url or "/prod-api/" in lower):
            return
        try:
            pd = req.post_data
            try: pd_json = json.loads(pd) if pd else None
            except: pd_json = {"_raw": pd[:3000] if pd else None}
        except: pd_json = None
        captured_requests.append({
            "ts": time.time(), "method": method, "url": url,
            "path_without_base": re.sub(r"^https?://[^/]+", "", url),
            "post_data": pd_json,
            "headers_subset": {k: v for k, v in req.headers.items() if k.lower() in {"authorization","content-type","clientid","tenant-id"}},
            "response": None,
        })

    def _on_resp(resp):
        req = resp.request
        if req.method.upper() == "GET": return
        url = req.url
        lower = url.lower()
        if any(x in lower for x in [".css", ".js", ".woff", ".ttf", ".eot", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", "websocket", "ws:"]):
            return
        if not (BASE_URL in url or "192.168." in url or "/prod-api/" in lower):
            return
        for cr in reversed(captured_requests):
            if cr["response"] is None and cr["method"] == req.method.upper() and cr["url"] == url:
                try:
                    status = resp.status
                    try: body = resp.json()
                    except:
                        try: body = {"_raw_text": resp.text()[:1500]}
                        except: body = None
                except: status = None; body = None
                cr["response"] = {"status": status, "body_sample": body}
                break

    page.on("request", _on_req)
    page.on("response", _on_resp)

def dump_buttons(page, label=""):
    try:
        return page.evaluate("""() => {
            const r = [];
            const tags = ['button','a','[role="button"]','.el-button','.ant-btn','span','div'];
            for (const sel of tags) {
                document.querySelectorAll(sel).forEach(el => {
                    if (!el.offsetParent) return;
                    const t = (el.innerText || el.textContent || '').replace(/\\s+/g,' ').trim();
                    if (!t || t.length > 30) return;
                    r.push(t);
                });
            }
            const seen = new Set(); const out = [];
            for (const b of r) { if (!seen.has(b)) { seen.add(b); out.push(b); } }
            return out.slice(0, 80);
        }""")
    except Exception as e:
        return [f"[ERROR dump buttons] {e}"]

def try_click_text(page, candidates):
    for txt in candidates:
        try:
            loc = page.get_by_text(txt, exact=True)
            if loc.count() > 0:
                loc.first.click(timeout=8000)
                return True, txt, f"点击成功：{txt}"
        except:
            try:
                loc = page.get_by_text(txt)
                if loc.count() > 0:
                    loc.first.click(timeout=8000)
                    return True, txt, f"点击成功（模糊）：{txt}"
            except: continue
    btns = dump_buttons(page)
    return False, "", f"未找到候选={candidates[:5]}，当前页可见按钮={btns[:30]}"

def try_fill_label(page, labels, value):
    for lb in labels:
        try:
            sel = page.get_by_label(lb)
            if sel.count(): sel.first.fill(value, timeout=3000); return True, lb
        except: pass
        try:
            sel = page.get_by_placeholder(lb)
            if sel.count(): sel.first.fill(value, timeout=3000); return True, lb
        except: pass
    return False, ""

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[FATAL] playwright 未安装"); sys.exit(2)

    with sync_playwright() as pw:
        CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        EDGE_PATH   = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        exe = CHROME_PATH if os.path.exists(CHROME_PATH) else EDGE_PATH if os.path.exists(EDGE_PATH) else None
        if not exe:
            print("[FATAL] 本机未找到 Chrome/Edge"); sys.exit(3)
        print(f"[INFO] 使用系统浏览器：{exe}")
        browser = pw.chromium.launch(headless=True, executable_path=exe)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="zh-CN")
        page = ctx.new_page()
        record_requests(page)

        steps = []

        # Step 0：登录
        print("[Step 0] 登录...")
        page.goto(BASE_URL, timeout=60000, wait_until="domcontentloaded")
        time.sleep(2)
        try: page.wait_for_load_state("networkidle", timeout=15000)
        except: pass
        try_fill_label(page, ["用户名", "账号", "用户", "请输入用户名", "请输入登录账号"], USERNAME)
        try_fill_label(page, ["密码", "请输入密码", "登录密码"], PASSWORD)
        try_click_text(page, ["登录", "登 录", "Sign in", "Login", "立即登录"])
        try: page.wait_for_load_state("networkidle", timeout=15000)
        except: pass
        time.sleep(3)
        print(f"[Step 0] 登录完成 URL={page.url}")
        steps.append({"step": "00_login", "url": page.url, "buttons": dump_buttons(page)[:30]})

        # Step 1：导航到项目管理→全部项目列表
        print("[Step 1] 导航到项目管理...")
        try_click_text(page, ["项目管理", "IPD项目", "我的项目", "项目列表", "项目中心"])
        try: page.wait_for_load_state("networkidle", timeout=15000)
        except: pass
        time.sleep(3)
        try_click_text(page, ["全部项目 →", "查看全部 →", "全部项目", "查看全部", "所有项目"])
        try: page.wait_for_load_state("networkidle", timeout=15000)
        except: pass
        time.sleep(3)
        list_btns = dump_buttons(page)
        print(f"[Step 1] 项目列表页 buttons={list_btns[:20]}")
        steps.append({"step": "01_list", "url": page.url, "buttons": list_btns[:40]})

        # Step 2：点第一个项目名称进入详情页
        print("[Step 2] 进入项目详情页...")
        # 项目列表里点项目名称（通常是一个 a 链接或 span）
        clicked_detail = False
        for text in ["查看", "详情", "查看详情"]:
            ok, txt, note = try_click_text(page, [text])
            if ok:
                clicked_detail = True
                break
        if not clicked_detail:
            # 直观点表格第一行的项目名称（可点击的蓝色链接）
            try:
                links = page.locator("a, .el-link, span[class*='link'], span[class*='clickable']")
                cnt = links.count()
                for i in range(min(cnt, 20)):
                    el = links.nth(i)
                    txt_val = el.inner_text(timeout=1000).strip()
                    if txt_val and len(txt_val) > 2 and len(txt_val) < 50 and txt_val not in ["新增", "导入", "导出", "重置", "搜索", "确 定", "取 消"]:
                        print(f"[Step 2] 点击表格链接：{txt_val}")
                        el.click(timeout=8000)
                        clicked_detail = True
                        break
            except Exception as e:
                print(f"[Step 2] 点链接失败：{e}")
        try: page.wait_for_load_state("networkidle", timeout=15000)
        except: pass
        time.sleep(3)
        detail_btns = dump_buttons(page)
        print(f"[Step 2] 详情页 buttons={detail_btns[:30]}")
        steps.append({"step": "02_detail", "url": page.url, "buttons": detail_btns[:50]})

        # Step 3：找编辑按钮并点击
        print("[Step 3] 找编辑按钮...")
        edit_candidates = [
            "编辑", "修 改", "修改", "编辑项目", "修改项目", "编辑信息", "修改信息",
            "Edit", "edit", "编辑基本信息", "修改基本信息", "编辑项目信息",
            "项目编辑", "项目修改", "更新", "更 新",
        ]
        ok_edit, txt_edit, note_edit = try_click_text(page, edit_candidates)
        print(f"[Step 3] 编辑按钮={ok_edit}:{txt_edit} | {note_edit}")
        time.sleep(2)
        try: page.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        edit_page_btns = dump_buttons(page)
        print(f"[Step 3] 编辑页/弹框 buttons={edit_page_btns[:30]}")
        steps.append({"step": "03_edit_click", "ok": ok_edit, "clicked": txt_edit, "note": note_edit, "url": page.url, "buttons": edit_page_btns[:40]})

        # Step 4：如果编辑弹框出来了，修改项目名称，然后点确定
        if ok_edit:
            print("[Step 4] 尝试修改项目名称...")
            time.sleep(1)
            # 找到项目名称输入框（el-input 或 label=项目名称）
            modified = False
            # 方式1：找 label=项目名称 的 input
            for lb in ["项目名称", "名称", "项目名"]:
                try:
                    inp = page.get_by_label(lb)
                    if inp.count() > 0:
                        old_val = inp.first.input_value(timeout=2000)
                        new_val = old_val + "-EDITED" if old_val else f"测试编辑-{time.strftime('%H%M%S')}"
                        inp.first.fill(new_val, timeout=3000)
                        modified = True
                        print(f"[Step 4] 修改 {lb}: {old_val} → {new_val}")
                        break
                except: pass
            # 方式2：找 placeholder 包含项目名称
            if not modified:
                for ph in ["请输入项目名称", "请输入名称", "项目名称"]:
                    try:
                        inp = page.get_by_placeholder(ph)
                        if inp.count() > 0:
                            old_val = inp.first.input_value(timeout=2000)
                            new_val = old_val + "-EDITED" if old_val else f"测试编辑-{time.strftime('%H%M%S')}"
                            inp.first.fill(new_val, timeout=3000)
                            modified = True
                            print(f"[Step 4] 修改 placeholder={ph}: {old_val} → {new_val}")
                            break
                    except: pass
            # 方式3：弹框内第一个可见 input
            if not modified:
                try:
                    inputs = page.locator(".el-dialog input[type='text'], .el-dialog input:not([type])")
                    if inputs.count() > 0:
                        old_val = inputs.first.input_value(timeout=2000)
                        new_val = old_val + "-EDITED" if old_val else f"测试编辑-{time.strftime('%H%M%S')}"
                        inputs.first.fill(new_val, timeout=3000)
                        modified = True
                        print(f"[Step 4] 修改弹框第1个input: {old_val} → {new_val}")
                except: pass

            steps.append({"step": "04_modify", "modified": modified, "url": page.url, "buttons": dump_buttons(page)[:30]})

            # Step 5：点确定/保存
            if modified:
                print("[Step 5] 点确定/保存...")
                time.sleep(0.5)
                ok_save, txt_save, note_save = try_click_text(page, [
                    "确 定", "确定", "保 存", "保存", "提交", "提 交", "确认修改", "确认",
                    "保存修改", "OK", "ok", "Save", "save",
                ])
                print(f"[Step 5] 保存按钮={ok_save}:{txt_save} | {note_save}")
                time.sleep(2)
                try: page.wait_for_load_state("networkidle", timeout=15000)
                except: pass
                steps.append({"step": "05_save", "ok": ok_save, "clicked": txt_save, "note": note_save, "url": page.url, "buttons": dump_buttons(page)[:30]})
        else:
            # 如果详情页没有编辑按钮=可能需要在列表页直接点编辑
            print("[Step 3-ALT] 详情页无编辑按钮，回列表页找编辑...")
            page.go_back()
            try: page.wait_for_load_state("networkidle", timeout=10000)
            except: pass
            time.sleep(2)
            # 列表页可能有编辑按钮（行操作列）
            ok_edit2, txt_edit2, note_edit2 = try_click_text(page, ["编辑", "修 改", "修改", "Edit"])
            print(f"[Step 3-ALT] 列表页编辑按钮={ok_edit2}:{txt_edit2} | {note_edit2}")
            time.sleep(1)
            steps.append({"step": "03_alt_list_edit", "ok": ok_edit2, "clicked": txt_edit2, "note": note_edit2, "buttons": dump_buttons(page)[:40]})

            if ok_edit2:
                print("[Step 4-ALT] 尝试修改项目名称...")
                time.sleep(1)
                modified = False
                for lb in ["项目名称", "名称", "项目名"]:
                    try:
                        inp = page.get_by_label(lb)
                        if inp.count() > 0:
                            old_val = inp.first.input_value(timeout=2000)
                            new_val = old_val + "-EDITED" if old_val else f"测试编辑-{time.strftime('%H%M%S')}"
                            inp.first.fill(new_val, timeout=3000)
                            modified = True
                            print(f"[Step 4-ALT] 修改 {lb}: {old_val} → {new_val}")
                            break
                    except: pass
                if not modified:
                    try:
                        inputs = page.locator(".el-dialog input[type='text'], .el-dialog input:not([type])")
                        if inputs.count() > 0:
                            old_val = inputs.first.input_value(timeout=2000)
                            new_val = old_val + "-EDITED" if old_val else f"测试编辑-{time.strftime('%H%M%S')}"
                            inputs.first.fill(new_val, timeout=3000)
                            modified = True
                            print(f"[Step 4-ALT] 修改弹框第1个input: {old_val} → {new_val}")
                    except: pass

                if modified:
                    print("[Step 5-ALT] 点确定/保存...")
                    time.sleep(0.5)
                    ok_save, txt_save, note_save = try_click_text(page, ["确 定", "确定", "保 存", "保存", "提交", "提 交", "确认修改", "确认"])
                    print(f"[Step 5-ALT] 保存按钮={ok_save}:{txt_save} | {note_save}")
                    time.sleep(2)
                    try: page.wait_for_load_state("networkidle", timeout=15000)
                    except: pass
                    steps.append({"step": "05_alt_save", "ok": ok_save, "clicked": txt_save, "note": note_save, "url": page.url, "buttons": dump_buttons(page)[:30]})

        # 截图
        shot = OUT_DIR / f"edit_capture_{int(time.time())}.png"
        try: page.screenshot(path=str(shot), full_page=True)
        except: pass

        browser.close()

    # 输出 manifest
    # 过滤出 UPDATE 候选请求（非 GET 且 path 包含 project）
    update_candidates = [r for r in captured_requests if "project" in r.get("path_without_base", "").lower()]
    manifest = {
        "capture_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "username": USERNAME,
        "steps": steps,
        "all_non_get_requests_count": len(captured_requests),
        "all_non_get_requests": captured_requests,
        "update_candidates": update_candidates,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OUTPUT] {MANIFEST}")
    print(f"[SUMMARY] 总非GET请求={len(captured_requests)}; project相关={len(update_candidates)}")
    print("\n===== 所有非 GET 请求 =====")
    for r in captured_requests:
        resp = r.get("response") or {}
        status = resp.get("status", "?")
        path = r.get("path_without_base", "")
        method = r.get("method", "")
        print(f"  {method} {path} → {status}")
    print("\n===== project 相关 UPDATE 候选 =====")
    for r in update_candidates:
        resp = r.get("response") or {}
        status = resp.get("status", "?")
        body = resp.get("body_sample", {})
        code = body.get("code", "?") if isinstance(body, dict) else "?"
        msg = body.get("msg", "")[:60] if isinstance(body, dict) else ""
        path = r.get("path_without_base", "")
        method = r.get("method", "")
        pd = r.get("post_data")
        pd_keys = list(pd.keys()) if isinstance(pd, dict) else str(pd)[:100] if pd else "None"
        print(f"  {method} {path} → HTTP={status} code={code} msg={msg} payload_keys={pd_keys}")

if __name__ == "__main__":
    main()
