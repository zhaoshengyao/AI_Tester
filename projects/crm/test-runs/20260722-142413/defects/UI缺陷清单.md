# UI缺陷清单

## 当前阶段
UI 自动化执行

## 输入文件
- docs/cases/功能测试用例-评审版.md
- docs/test-runs/20260722-142413/reports/UI自动化覆盖矩阵.md
- docs/test-runs/20260722-142413/reports/UI自动化测试报告.md

## 产出文件
- docs/test-runs/20260722-142413/defects/UI缺陷清单.md

## 正文/核心内容
- 测试批次：20260722-142413
- 执行状态：失败
- 退出码：1
- 失败用例数：12
- 结论摘要：本轮 UI 自动化存在 12 条失败用例，详见下方缺陷明细表。
- 证据入口：
  - docs/test-runs/20260722-142413/reports/UI自动化测试报告.md
  - tests/ui/reports/html/
  - tests/ui/reports/raw/result.json

## 缺陷明细
| 序号 | 模块 | 用例编号 | 用例标题 | 缺陷类型 | 耗时(ms) | 错误摘要 |\n| --- | --- | --- | --- | --- | ---: | --- |\n| 1 | business-crud.spec | FUNC-BUSINESS-001 | 创建商机-填写完整信息 | 断言失败 | 16291 | Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoContain[2m([22m[32mexpected[39m[2m) // indexOf[22m  Expected substring: [32m"成功"[39m Received string:    [31m""[39m    34 /        35 / ... |\n| 2 | business-crud.spec | FUNC-BUSINESS-002 | 创建商机-必填字段校验 | 断言失败 | 8933 | TypeError: [2mexpect([22m[31mreceived[39m[2m).[22mtoMatch[2m([22m[32mexpected[39m[2m)[22m  [1mMatcher error[22m: [31mreceived[39m value must be a string  Received has value: [31mnull... |\n| 3 | business-flow.spec |  | FLOW-001 创建线索并转化为商机 | 断言失败 | 57508 | TimeoutError: locator.waitFor: Timeout 10000ms exceeded. Call log: [2m  - waiting for locator('.el-overlay-dialog').first().locator('input[placeholder="请输入线索名称"]') to be visible[22m      at ..\pages... |\n| 4 | business-flow.spec |  | FLOW-002 从线索创建商机 | 断言失败 | 35094 | TimeoutError: locator.waitFor: Timeout 10000ms exceeded. Call log: [2m  - waiting for locator('.el-dialog').first().locator('input[placeholder="请输入联系人"]') to be visible[22m      at ..\pages\BasePage... |\n| 5 | business-flow.spec |  | FLOW-003 从商机创建报价 | 断言失败 | 24052 | Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoContain[2m([22m[32mexpected[39m[2m) // indexOf[22m  Expected substring: [32m"成功"[39m Received string:    [31m""[39m    56 /     const di... |\n| 6 | clue-crud.spec | FUNC-CLUE-001 | 创建线索-填写完整信息 | 断言失败 | 52341 | TimeoutError: locator.waitFor: Timeout 10000ms exceeded. Call log: [2m  - waiting for locator('.el-overlay-dialog').first().locator('input[placeholder="请输入线索名称"]') to be visible[22m      at ..\pages... |\n| 7 | clue-crud.spec | FUNC-CLUE-002 | 创建线索-必填字段校验 | 断言失败 | 44572 | Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoMatch[2m([22m[32mexpected[39m[2m)[22m  Expected pattern: [32m/不能为空/必填/[39m Received string:  [31m"请输入搜索关键词"[39m    41 /   42 /   test('F... |\n| 8 | crm-crud.spec |  | FUNC-CRM-CUST-001 创建客户-填写完整信息 | 断言失败 | 39100 | Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoContain[2m([22m[32mexpected[39m[2m) // indexOf[22m  Expected substring: [32m"成功"[39m Received string:    [31m"请输入搜索关键词"[39m    19 /     ... |\n| 9 | product-crud.spec | FUNC-PRODUCT-001 | 创建产品-填写完整信息 | 断言失败 | 53472 | Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoContain[2m([22m[32mexpected[39m[2m) // indexOf[22m  Expected substring: [32m"成功"[39m Received string:    [31m"请输入搜索关键词"[39m    34 /     ... |\n| 10 | product-crud.spec | FUNC-PRODUCT-002 | 创建产品-必填字段校验 | 断言失败 | 39314 | Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoMatch[2m([22m[32mexpected[39m[2m)[22m  Expected pattern: [32m/不能为空/必填/[39m Received string:  [31m"请输入搜索关键词"[39m    41 /   42 /   test('F... |\n| 11 | quotation-crud.spec | FUNC-QUO-001 | 创建报价-填写完整信息 | 断言失败 | 23608 | Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoContain[2m([22m[32mexpected[39m[2m) // indexOf[22m  Expected substring: [32m"成功"[39m Received string:    [31m""[39m    25 /   26 /     c... |\n| 12 | quotation-crud.spec | FUNC-QUO-002 | 创建报价-必填字段校验 | 断言失败 | 15504 | Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoMatch[2m([22m[32mexpected[39m[2m)[22m  Expected pattern: [32m/不能为空/必填/[39m Received string:  [31m""[39m    38 /     if (!isAvailable) { ... |\n

## 执行结论
- 当前缺陷登记状态：失败。

## 风险与待确认项
- Playwright 执行失败或存在失败用例，请结合 HTML/JSON 报告定位。

## 下一步建议
- 如有失败用例，补充或更新正式 UI 缺陷。
- 如未执行，先恢复前端地址、浏览器或依赖后再执行。
