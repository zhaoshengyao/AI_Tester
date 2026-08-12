# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: crm\clue-crud.spec.ts >> 线索管理 CRUD 测试 >> FUNC-CLUE-001 创建线索-填写完整信息
- Location: specs\crm\clue-crud.spec.ts:25:18

# Error details

```
TimeoutError: locator.waitFor: Timeout 10000ms exceeded.
Call log:
  - waiting for locator('.el-overlay-dialog').first().locator('input[placeholder="请输入线索名称"]') to be visible

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e4]:
    - link "治为CRM管理系统" [ref=e6] [cursor=pointer]:
      - /url: /
      - heading "治为CRM管理系统" [level=1] [ref=e7]
    - menubar [ref=e11]:
      - link "首页" [ref=e13] [cursor=pointer]:
        - /url: /index
        - menuitem "首页" [ref=e14]:
          - img [ref=e15]
          - generic [ref=e17]: 首页
      - link "管理驾驶舱" [ref=e19] [cursor=pointer]:
        - /url: /bossWorkbench
        - menuitem "管理驾驶舱" [ref=e20]:
          - img [ref=e21]
          - generic [ref=e23]: 管理驾驶舱
      - link "工作台首页" [ref=e25] [cursor=pointer]:
        - /url: /salesWorkbench
        - menuitem "工作台首页" [ref=e26]:
          - img [ref=e27]
          - generic [ref=e29]: 工作台首页
      - link "团队看板" [ref=e31] [cursor=pointer]:
        - /url: /board
        - menuitem "团队看板" [ref=e32]:
          - img [ref=e33]
          - generic [ref=e35]: 团队看板
      - link "我的待办" [ref=e37] [cursor=pointer]:
        - /url: /myAgenda
        - menuitem "我的待办" [ref=e38]:
          - img [ref=e39]
          - generic [ref=e41]: 我的待办
      - menuitem "绩效管理" [ref=e43]:
        - generic [ref=e44] [cursor=pointer]:
          - img [ref=e45]
          - generic [ref=e47]: 绩效管理
          - img [ref=e49]
      - menuitem "营销管理" [expanded] [ref=e52]:
        - generic [ref=e53] [cursor=pointer]:
          - img [ref=e54]
          - generic [ref=e56]: 营销管理
          - img [ref=e58]
        - menu [ref=e60]:
          - link "线索池" [ref=e62] [cursor=pointer]:
            - /url: /marketing/clue
            - menuitem "线索池" [ref=e63]:
              - img [ref=e64]
              - generic [ref=e66]: 线索池
          - link "我的线索" [ref=e68] [cursor=pointer]:
            - /url: /marketing/clue/mine
            - menuitem "我的线索" [ref=e69]:
              - img [ref=e70]
              - generic [ref=e72]: 我的线索
      - menuitem "客户管理" [ref=e74]:
        - generic [ref=e75] [cursor=pointer]:
          - img [ref=e76]
          - generic [ref=e78]: 客户管理
          - img [ref=e80]
      - link "报表中心" [ref=e83] [cursor=pointer]:
        - /url: /report
        - menuitem "报表中心" [ref=e84]:
          - img [ref=e85]
          - generic [ref=e87]: 报表中心
      - menuitem "商机管理" [ref=e89]:
        - generic [ref=e90] [cursor=pointer]:
          - img [ref=e91]
          - generic [ref=e93]: 商机管理
          - img [ref=e95]
      - menuitem "报价管理" [ref=e98]:
        - generic [ref=e99] [cursor=pointer]:
          - img [ref=e100]
          - generic [ref=e102]: 报价管理
          - img [ref=e104]
      - menuitem "产品管理" [ref=e107]:
        - generic [ref=e108] [cursor=pointer]:
          - img [ref=e109]
          - generic [ref=e111]: 产品管理
          - img [ref=e113]
      - menuitem "设置中心" [ref=e116]:
        - generic [ref=e117] [cursor=pointer]:
          - img [ref=e118]
          - generic [ref=e120]: 设置中心
          - img [ref=e122]
      - menuitem "系统管理" [ref=e125]:
        - generic [ref=e126] [cursor=pointer]:
          - img [ref=e127]
          - generic [ref=e129]: 系统管理
          - img [ref=e131]
      - menuitem "系统监控" [ref=e134]:
        - generic [ref=e135] [cursor=pointer]:
          - img [ref=e136]
          - generic [ref=e138]: 系统监控
          - img [ref=e140]
  - generic [ref=e142]:
    - generic [ref=e143]:
      - generic [ref=e144]:
        - img [ref=e146] [cursor=pointer]
        - navigation "面包屑" [ref=e148]:
          - generic [ref=e149]:
            - link "首页" [ref=e150]
            - text: /
          - generic [ref=e151]:
            - link "营销管理" [ref=e152]
            - text: /
          - link "线索池" [ref=e154]
        - generic [ref=e155]:
          - generic [ref=e157]:
            - generic [ref=e159] [cursor=pointer]:
              - generic:
                - combobox [ref=e161]
                - generic [ref=e162]: 全部
              - img [ref=e165]
            - generic [ref=e167]:
              - textbox "搜索客户/线索/商机..." [ref=e169]
              - button "搜索" [ref=e171] [cursor=pointer]:
                - generic [ref=e172]: 搜索
          - generic [ref=e173]:
            - button "新建线索" [active] [ref=e174] [cursor=pointer]:
              - img [ref=e176]
              - generic [ref=e178]: 新建线索
            - button "新增跟进" [ref=e179] [cursor=pointer]:
              - img [ref=e181]
              - generic [ref=e184]: 新增跟进
            - button "添加客户" [ref=e185] [cursor=pointer]:
              - img [ref=e187]
              - generic [ref=e189]: 添加客户
            - button "新建商机" [ref=e190] [cursor=pointer]:
              - img [ref=e192]
              - generic [ref=e196]: 新建商机
            - button "创建报价" [ref=e197] [cursor=pointer]:
              - img [ref=e199]
              - generic [ref=e201]: 创建报价
        - generic [ref=e202]:
          - img [ref=e206] [cursor=pointer]
          - button "赵生尧 管理员,企微,销售主管,普通销售" [ref=e210] [cursor=pointer]:
            - img [ref=e211]
            - generic [ref=e212]:
              - generic [ref=e213]: 赵生尧
              - generic [ref=e214]: 管理员,企微,销售主管,普通销售
            - img [ref=e216]
      - generic [ref=e221]:
        - link "首页" [ref=e222] [cursor=pointer]:
          - /url: /index
        - link "线索池" [ref=e223] [cursor=pointer]:
          - /url: /marketing/clue
          - text: 线索池
          - img [ref=e225]
    - generic [ref=e228]:
      - generic [ref=e232]:
        - generic [ref=e233]:
          - generic [ref=e234]: 线索编码
          - textbox "线索编码" [ref=e238]:
            - /placeholder: 请输入线索编码
        - generic [ref=e239]:
          - generic [ref=e240]: 公司名称
          - textbox "公司名称" [ref=e244]:
            - /placeholder: 请输入公司名称
        - generic [ref=e245]:
          - generic [ref=e246]: 线索名称
          - textbox "线索名称" [ref=e250]:
            - /placeholder: 请输入线索名称
        - generic [ref=e251]:
          - generic [ref=e252]: 线索来源
          - generic [ref=e255] [cursor=pointer]:
            - generic:
              - combobox "线索来源" [ref=e257]
              - generic [ref=e258]: 线索来源
            - img [ref=e261]
        - generic [ref=e263]:
          - generic [ref=e264]: 线索状态
          - generic [ref=e267] [cursor=pointer]:
            - generic:
              - combobox "线索状态" [ref=e269]
              - generic [ref=e270]: 线索状态
            - img [ref=e273]
        - generic [ref=e276]:
          - button "搜索" [ref=e277] [cursor=pointer]:
            - img [ref=e279]
            - generic [ref=e281]: 搜索
          - button "重置" [ref=e282] [cursor=pointer]:
            - img [ref=e284]
            - generic [ref=e286]: 重置
      - generic [ref=e287]:
        - generic [ref=e289]:
          - button "新增" [ref=e291] [cursor=pointer]:
            - img [ref=e293]
            - generic [ref=e295]: 新增
          - button "修改" [disabled] [ref=e297]:
            - img [ref=e299]
            - generic [ref=e302]: 修改
          - button "删除" [disabled] [ref=e304]:
            - img [ref=e306]
            - generic [ref=e308]: 删除
          - button "导出" [ref=e310] [cursor=pointer]:
            - img [ref=e312]
            - generic [ref=e314]: 导出
          - button "导入" [ref=e316] [cursor=pointer]:
            - img [ref=e318]
            - generic [ref=e320]: 导入
          - generic [ref=e322]:
            - button [ref=e323] [cursor=pointer]:
              - img [ref=e325]
            - button [ref=e327] [cursor=pointer]:
              - img [ref=e329]
        - generic [ref=e331]:
          - generic [ref=e333]:
            - table [ref=e335]:
              - rowgroup [ref=e349]:
                - row "选择所有行 线索编码 公司名称 线索名称 线索来源 预计金额 负责人 线索状态 联系人 联系电话 1级行业 操作" [ref=e350]:
                  - columnheader "选择所有行" [ref=e351]:
                    - generic "选择所有行" [ref=e353] [cursor=pointer]:
                      - generic [ref=e354]:
                        - checkbox "选择所有行"
                  - columnheader "线索编码" [ref=e356]:
                    - generic [ref=e357]: 线索编码
                  - columnheader "公司名称" [ref=e358]:
                    - generic [ref=e359]: 公司名称
                  - columnheader "线索名称" [ref=e360]:
                    - generic [ref=e361]: 线索名称
                  - columnheader "线索来源" [ref=e362]:
                    - generic [ref=e363]: 线索来源
                  - columnheader "预计金额" [ref=e364]:
                    - generic [ref=e365]: 预计金额
                  - columnheader "负责人" [ref=e366]:
                    - generic [ref=e367]: 负责人
                  - columnheader "线索状态" [ref=e368]:
                    - generic [ref=e369]: 线索状态
                  - columnheader "联系人" [ref=e370]:
                    - generic [ref=e371]: 联系人
                  - columnheader "联系电话" [ref=e372]:
                    - generic [ref=e373]: 联系电话
                  - columnheader "1级行业" [ref=e374]:
                    - generic [ref=e375]: 1级行业
                  - columnheader "操作" [ref=e376]:
                    - generic [ref=e377]: 操作
            - table [ref=e382]:
              - rowgroup [ref=e396]:
                - row "选择当前行 XSL_202607220002 测试线索_gqtyzPlxJz - - 待跟进 - 查看 领取 修改 删除" [ref=e397]:
                  - cell "选择当前行" [ref=e398]:
                    - generic "选择当前行" [ref=e400] [cursor=pointer]:
                      - generic [ref=e401]:
                        - checkbox "选择当前行"
                  - cell "XSL_202607220002" [ref=e403]:
                    - generic [ref=e404]: XSL_202607220002
                  - cell [ref=e405]
                  - cell "测试线索_gqtyzPlxJz" [ref=e406]:
                    - generic [ref=e407]: 测试线索_gqtyzPlxJz
                  - cell "-" [ref=e408]:
                    - generic [ref=e409]: "-"
                  - cell "-" [ref=e410]:
                    - generic [ref=e411]: "-"
                  - cell [ref=e412]
                  - cell "待跟进" [ref=e413]:
                    - generic [ref=e417]: 待跟进
                  - cell [ref=e418]
                  - cell [ref=e419]
                  - cell "-" [ref=e420]:
                    - generic [ref=e421]: "-"
                  - cell "查看 领取 修改 删除" [ref=e422]:
                    - generic [ref=e423]:
                      - button "查看" [ref=e424] [cursor=pointer]:
                        - generic [ref=e425]: 查看
                      - button "领取" [ref=e426] [cursor=pointer]:
                        - generic [ref=e427]: 领取
                      - button "修改" [ref=e428] [cursor=pointer]:
                        - generic [ref=e429]: 修改
                      - button "删除" [ref=e430] [cursor=pointer]:
                        - generic [ref=e431]: 删除
                - row "选择当前行 XSL_202607220001 测试线索_xd3AO3Enl4 - - 待跟进 - 查看 领取 修改 删除" [ref=e432]:
                  - cell "选择当前行" [ref=e433]:
                    - generic "选择当前行" [ref=e435] [cursor=pointer]:
                      - generic [ref=e436]:
                        - checkbox "选择当前行"
                  - cell "XSL_202607220001" [ref=e438]:
                    - generic [ref=e439]: XSL_202607220001
                  - cell [ref=e440]
                  - cell "测试线索_xd3AO3Enl4" [ref=e441]:
                    - generic [ref=e442]: 测试线索_xd3AO3Enl4
                  - cell "-" [ref=e443]:
                    - generic [ref=e444]: "-"
                  - cell "-" [ref=e445]:
                    - generic [ref=e446]: "-"
                  - cell [ref=e447]
                  - cell "待跟进" [ref=e448]:
                    - generic [ref=e452]: 待跟进
                  - cell [ref=e453]
                  - cell [ref=e454]
                  - cell "-" [ref=e455]:
                    - generic [ref=e456]: "-"
                  - cell "查看 领取 修改 删除" [ref=e457]:
                    - generic [ref=e458]:
                      - button "查看" [ref=e459] [cursor=pointer]:
                        - generic [ref=e460]: 查看
                      - button "领取" [ref=e461] [cursor=pointer]:
                        - generic [ref=e462]: 领取
                      - button "修改" [ref=e463] [cursor=pointer]:
                        - generic [ref=e464]: 修改
                      - button "删除" [ref=e465] [cursor=pointer]:
                        - generic [ref=e466]: 删除
                - row "选择当前行 XSL_202607210009 测试线索_16qXMz4ilR - - 待跟进 - 查看 领取 修改 删除" [ref=e467]:
                  - cell "选择当前行" [ref=e468]:
                    - generic "选择当前行" [ref=e470] [cursor=pointer]:
                      - generic [ref=e471]:
                        - checkbox "选择当前行"
                  - cell "XSL_202607210009" [ref=e473]:
                    - generic [ref=e474]: XSL_202607210009
                  - cell [ref=e475]
                  - cell "测试线索_16qXMz4ilR" [ref=e476]:
                    - generic [ref=e477]: 测试线索_16qXMz4ilR
                  - cell "-" [ref=e478]:
                    - generic [ref=e479]: "-"
                  - cell "-" [ref=e480]:
                    - generic [ref=e481]: "-"
                  - cell [ref=e482]
                  - cell "待跟进" [ref=e483]:
                    - generic [ref=e487]: 待跟进
                  - cell [ref=e488]
                  - cell [ref=e489]
                  - cell "-" [ref=e490]:
                    - generic [ref=e491]: "-"
                  - cell "查看 领取 修改 删除" [ref=e492]:
                    - generic [ref=e493]:
                      - button "查看" [ref=e494] [cursor=pointer]:
                        - generic [ref=e495]: 查看
                      - button "领取" [ref=e496] [cursor=pointer]:
                        - generic [ref=e497]: 领取
                      - button "修改" [ref=e498] [cursor=pointer]:
                        - generic [ref=e499]: 修改
                      - button "删除" [ref=e500] [cursor=pointer]:
                        - generic [ref=e501]: 删除
                - row "选择当前行 XSL_202607210008 测试线索_NGX0ezjf2q - - 待跟进 - 查看 领取 修改 删除" [ref=e502]:
                  - cell "选择当前行" [ref=e503]:
                    - generic "选择当前行" [ref=e505] [cursor=pointer]:
                      - generic [ref=e506]:
                        - checkbox "选择当前行"
                  - cell "XSL_202607210008" [ref=e508]:
                    - generic [ref=e509]: XSL_202607210008
                  - cell [ref=e510]
                  - cell "测试线索_NGX0ezjf2q" [ref=e511]:
                    - generic [ref=e512]: 测试线索_NGX0ezjf2q
                  - cell "-" [ref=e513]:
                    - generic [ref=e514]: "-"
                  - cell "-" [ref=e515]:
                    - generic [ref=e516]: "-"
                  - cell [ref=e517]
                  - cell "待跟进" [ref=e518]:
                    - generic [ref=e522]: 待跟进
                  - cell [ref=e523]
                  - cell [ref=e524]
                  - cell "-" [ref=e525]:
                    - generic [ref=e526]: "-"
                  - cell "查看 领取 修改 删除" [ref=e527]:
                    - generic [ref=e528]:
                      - button "查看" [ref=e529] [cursor=pointer]:
                        - generic [ref=e530]: 查看
                      - button "领取" [ref=e531] [cursor=pointer]:
                        - generic [ref=e532]: 领取
                      - button "修改" [ref=e533] [cursor=pointer]:
                        - generic [ref=e534]: 修改
                      - button "删除" [ref=e535] [cursor=pointer]:
                        - generic [ref=e536]: 删除
                - row "选择当前行 XSL_202607210007 测试线索_5PJd5nhV2n - - 待跟进 - 查看 领取 修改 删除" [ref=e537]:
                  - cell "选择当前行" [ref=e538]:
                    - generic "选择当前行" [ref=e540] [cursor=pointer]:
                      - generic [ref=e541]:
                        - checkbox "选择当前行"
                  - cell "XSL_202607210007" [ref=e543]:
                    - generic [ref=e544]: XSL_202607210007
                  - cell [ref=e545]
                  - cell "测试线索_5PJd5nhV2n" [ref=e546]:
                    - generic [ref=e547]: 测试线索_5PJd5nhV2n
                  - cell "-" [ref=e548]:
                    - generic [ref=e549]: "-"
                  - cell "-" [ref=e550]:
                    - generic [ref=e551]: "-"
                  - cell [ref=e552]
                  - cell "待跟进" [ref=e553]:
                    - generic [ref=e557]: 待跟进
                  - cell [ref=e558]
                  - cell [ref=e559]
                  - cell "-" [ref=e560]:
                    - generic [ref=e561]: "-"
                  - cell "查看 领取 修改 删除" [ref=e562]:
                    - generic [ref=e563]:
                      - button "查看" [ref=e564] [cursor=pointer]:
                        - generic [ref=e565]: 查看
                      - button "领取" [ref=e566] [cursor=pointer]:
                        - generic [ref=e567]: 领取
                      - button "修改" [ref=e568] [cursor=pointer]:
                        - generic [ref=e569]: 修改
                      - button "删除" [ref=e570] [cursor=pointer]:
                        - generic [ref=e571]: 删除
                - row "选择当前行 XSL_202607210006 测试线索_gf0laiBg82 - - 待跟进 - 查看 领取 修改 删除" [ref=e572]:
                  - cell "选择当前行" [ref=e573]:
                    - generic "选择当前行" [ref=e575] [cursor=pointer]:
                      - generic [ref=e576]:
                        - checkbox "选择当前行"
                  - cell "XSL_202607210006" [ref=e578]:
                    - generic [ref=e579]: XSL_202607210006
                  - cell [ref=e580]
                  - cell "测试线索_gf0laiBg82" [ref=e581]:
                    - generic [ref=e582]: 测试线索_gf0laiBg82
                  - cell "-" [ref=e583]:
                    - generic [ref=e584]: "-"
                  - cell "-" [ref=e585]:
                    - generic [ref=e586]: "-"
                  - cell [ref=e587]
                  - cell "待跟进" [ref=e588]:
                    - generic [ref=e592]: 待跟进
                  - cell [ref=e593]
                  - cell [ref=e594]
                  - cell "-" [ref=e595]:
                    - generic [ref=e596]: "-"
                  - cell "查看 领取 修改 删除" [ref=e597]:
                    - generic [ref=e598]:
                      - button "查看" [ref=e599] [cursor=pointer]:
                        - generic [ref=e600]: 查看
                      - button "领取" [ref=e601] [cursor=pointer]:
                        - generic [ref=e602]: 领取
                      - button "修改" [ref=e603] [cursor=pointer]:
                        - generic [ref=e604]: 修改
                      - button "删除" [ref=e605] [cursor=pointer]:
                        - generic [ref=e606]: 删除
                - row "选择当前行 XSL_202607210005 测试线索_4FF60HSLsQ - - 待跟进 - 查看 领取 修改 删除" [ref=e607]:
                  - cell "选择当前行" [ref=e608]:
                    - generic "选择当前行" [ref=e610] [cursor=pointer]:
                      - generic [ref=e611]:
                        - checkbox "选择当前行"
                  - cell "XSL_202607210005" [ref=e613]:
                    - generic [ref=e614]: XSL_202607210005
                  - cell [ref=e615]
                  - cell "测试线索_4FF60HSLsQ" [ref=e616]:
                    - generic [ref=e617]: 测试线索_4FF60HSLsQ
                  - cell "-" [ref=e618]:
                    - generic [ref=e619]: "-"
                  - cell "-" [ref=e620]:
                    - generic [ref=e621]: "-"
                  - cell [ref=e622]
                  - cell "待跟进" [ref=e623]:
                    - generic [ref=e627]: 待跟进
                  - cell [ref=e628]
                  - cell [ref=e629]
                  - cell "-" [ref=e630]:
                    - generic [ref=e631]: "-"
                  - cell "查看 领取 修改 删除" [ref=e632]:
                    - generic [ref=e633]:
                      - button "查看" [ref=e634] [cursor=pointer]:
                        - generic [ref=e635]: 查看
                      - button "领取" [ref=e636] [cursor=pointer]:
                        - generic [ref=e637]: 领取
                      - button "修改" [ref=e638] [cursor=pointer]:
                        - generic [ref=e639]: 修改
                      - button "删除" [ref=e640] [cursor=pointer]:
                        - generic [ref=e641]: 删除
                - row "选择当前行 XSL_202607210004 测试线索_7wlt54LgJ2 - - 待跟进 - 查看 领取 修改 删除" [ref=e642]:
                  - cell "选择当前行" [ref=e643]:
                    - generic "选择当前行" [ref=e645] [cursor=pointer]:
                      - generic [ref=e646]:
                        - checkbox "选择当前行"
                  - cell "XSL_202607210004" [ref=e648]:
                    - generic [ref=e649]: XSL_202607210004
                  - cell [ref=e650]
                  - cell "测试线索_7wlt54LgJ2" [ref=e651]:
                    - generic [ref=e652]: 测试线索_7wlt54LgJ2
                  - cell "-" [ref=e653]:
                    - generic [ref=e654]: "-"
                  - cell "-" [ref=e655]:
                    - generic [ref=e656]: "-"
                  - cell [ref=e657]
                  - cell "待跟进" [ref=e658]:
                    - generic [ref=e662]: 待跟进
                  - cell [ref=e663]
                  - cell [ref=e664]
                  - cell "-" [ref=e665]:
                    - generic [ref=e666]: "-"
                  - cell "查看 领取 修改 删除" [ref=e667]:
                    - generic [ref=e668]:
                      - button "查看" [ref=e669] [cursor=pointer]:
                        - generic [ref=e670]: 查看
                      - button "领取" [ref=e671] [cursor=pointer]:
                        - generic [ref=e672]: 领取
                      - button "修改" [ref=e673] [cursor=pointer]:
                        - generic [ref=e674]: 修改
                      - button "删除" [ref=e675] [cursor=pointer]:
                        - generic [ref=e676]: 删除
                - row "选择当前行 XSL_202607210003 测试线索_ih48i8z0lL - - 待跟进 - 查看 领取 修改 删除" [ref=e677]:
                  - cell "选择当前行" [ref=e678]:
                    - generic "选择当前行" [ref=e680] [cursor=pointer]:
                      - generic [ref=e681]:
                        - checkbox "选择当前行"
                  - cell "XSL_202607210003" [ref=e683]:
                    - generic [ref=e684]: XSL_202607210003
                  - cell [ref=e685]
                  - cell "测试线索_ih48i8z0lL" [ref=e686]:
                    - generic [ref=e687]: 测试线索_ih48i8z0lL
                  - cell "-" [ref=e688]:
                    - generic [ref=e689]: "-"
                  - cell "-" [ref=e690]:
                    - generic [ref=e691]: "-"
                  - cell [ref=e692]
                  - cell "待跟进" [ref=e693]:
                    - generic [ref=e697]: 待跟进
                  - cell [ref=e698]
                  - cell [ref=e699]
                  - cell "-" [ref=e700]:
                    - generic [ref=e701]: "-"
                  - cell "查看 领取 修改 删除" [ref=e702]:
                    - generic [ref=e703]:
                      - button "查看" [ref=e704] [cursor=pointer]:
                        - generic [ref=e705]: 查看
                      - button "领取" [ref=e706] [cursor=pointer]:
                        - generic [ref=e707]: 领取
                      - button "修改" [ref=e708] [cursor=pointer]:
                        - generic [ref=e709]: 修改
                      - button "删除" [ref=e710] [cursor=pointer]:
                        - generic [ref=e711]: 删除
                - row "选择当前行 XSL_202607210002 测试线索_fiC6cbZsoU - - 待跟进 - 查看 领取 修改 删除" [ref=e712]:
                  - cell "选择当前行" [ref=e713]:
                    - generic "选择当前行" [ref=e715] [cursor=pointer]:
                      - generic [ref=e716]:
                        - checkbox "选择当前行"
                  - cell "XSL_202607210002" [ref=e718]:
                    - generic [ref=e719]: XSL_202607210002
                  - cell [ref=e720]
                  - cell "测试线索_fiC6cbZsoU" [ref=e721]:
                    - generic [ref=e722]: 测试线索_fiC6cbZsoU
                  - cell "-" [ref=e723]:
                    - generic [ref=e724]: "-"
                  - cell "-" [ref=e725]:
                    - generic [ref=e726]: "-"
                  - cell [ref=e727]
                  - cell "待跟进" [ref=e728]:
                    - generic [ref=e732]: 待跟进
                  - cell [ref=e733]
                  - cell [ref=e734]
                  - cell "-" [ref=e735]:
                    - generic [ref=e736]: "-"
                  - cell "查看 领取 修改 删除" [ref=e737]:
                    - generic [ref=e738]:
                      - button "查看" [ref=e739] [cursor=pointer]:
                        - generic [ref=e740]: 查看
                      - button "领取" [ref=e741] [cursor=pointer]:
                        - generic [ref=e742]: 领取
                      - button "修改" [ref=e743] [cursor=pointer]:
                        - generic [ref=e744]: 修改
                      - button "删除" [ref=e745] [cursor=pointer]:
                        - generic [ref=e746]: 删除
          - generic [ref=e748]:
            - generic [ref=e749]: 共 87 条
            - generic [ref=e752] [cursor=pointer]:
              - generic:
                - combobox [ref=e754]
                - generic [ref=e755]: 10条/页
              - img [ref=e758]
            - button "上一页" [disabled] [ref=e760]:
              - generic:
                - img
            - list [ref=e761]:
              - listitem "第 1 页" [ref=e762]: "1"
              - listitem "第 2 页" [ref=e763] [cursor=pointer]: "2"
              - listitem "第 3 页" [ref=e764] [cursor=pointer]: "3"
              - listitem "第 4 页" [ref=e765] [cursor=pointer]: "4"
              - listitem "第 5 页" [ref=e766] [cursor=pointer]: "5"
              - listitem "第 6 页" [ref=e767] [cursor=pointer]: "6"
              - listitem "向后 5 页" [ref=e768] [cursor=pointer]:
                - img
              - listitem "第 9 页" [ref=e769] [cursor=pointer]: "9"
            - button "下一页" [ref=e770] [cursor=pointer]:
              - generic:
                - img
            - generic [ref=e771]:
              - generic [ref=e772]: 前往
              - spinbutton "页" [ref=e775]: "1"
              - generic [ref=e776]: 页
```

# Test source

```ts
  170 |     const selectors = ['.el-dialog', '[role="dialog"]', '.el-drawer'];
  171 | 
  172 |     for (const selector of selectors) {
  173 |       let dialog: Locator;
  174 |       if (titleText) {
  175 |         dialog = this.page.locator(selector).filter({ hasText: titleText }).first();
  176 |       } else {
  177 |         dialog = this.page.locator(selector).first();
  178 |       }
  179 | 
  180 |       if ((await dialog.count()) > 0) {
  181 |         try {
  182 |           await dialog.waitFor({ state: 'visible', timeout: 15000 });
  183 |           console.log(`✅ 弹窗已打开: ${selector}`);
  184 |           return dialog;
  185 |         } catch {
  186 |           console.log(`⚠️ 弹窗 ${selector} 等待超时，尝试下一个选择器`);
  187 |         }
  188 |       }
  189 |     }
  190 | 
  191 |     console.log(`⚠️ 尝试所有选择器均未找到可见弹窗，等待页面响应...`);
  192 |     await this.page.waitForTimeout(2000);
  193 | 
  194 |     const visibleContent = this.page.locator('.el-dialog__body:visible, .el-drawer__body:visible');
  195 |     if ((await visibleContent.count()) > 0) {
  196 |       const wrapper = visibleContent.locator('..').locator('..').first();
  197 |       console.log(`✅ 通过内容区域找到弹窗/抽屉`);
  198 |       return wrapper;
  199 |     }
  200 | 
  201 |     const dialogInfo = await this.page.evaluate(() => {
  202 |       const overlays = document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer');
  203 |       const results: Array<{ index: number; class: string; isVisible: boolean }> = [];
  204 |       overlays.forEach((el: Element, index: number) => {
  205 |         const style = window.getComputedStyle(el);
  206 |         results.push({
  207 |           index,
  208 |           class: el.className,
  209 |           isVisible: style.display !== 'none' && style.visibility !== 'hidden'
  210 |         });
  211 |       });
  212 |       return results;
  213 |     });
  214 | 
  215 |     const visibleDialogs = dialogInfo.filter(d => d.isVisible);
  216 |     if (visibleDialogs.length > 0) {
  217 |       const selector = `.${visibleDialogs[0].class.split(' ').filter(c => c).join('.')}`;
  218 |       console.log(`✅ JS检测到可见弹窗: ${selector}`);
  219 |       return this.page.locator(selector).first();
  220 |     }
  221 | 
  222 |     throw new Error('未找到弹窗');
  223 |   }
  224 | 
  225 |   async clickTableRow(rowIndex: number = 0): Promise<void> {
  226 |     const rows = this.page.locator('.el-table__row');
  227 |     if ((await rows.count()) > rowIndex) {
  228 |       await rows.nth(rowIndex).click();
  229 |       console.log(`✅ 点击第 ${rowIndex + 1} 行`);
  230 |     } else {
  231 |       console.log('⚠️ 未找到表格行');
  232 |     }
  233 |   }
  234 | 
  235 |   async goToPage(pageNumber: number): Promise<void> {
  236 |     const pagination = this.page.locator('.el-pagination').first();
  237 |     if ((await pagination.count()) > 0 && await pagination.isVisible()) {
  238 |       const pageButton = pagination.locator('button').filter({ hasText: String(pageNumber) }).first();
  239 |       if ((await pageButton.count()) > 0 && await pageButton.isVisible()) {
  240 |         await pageButton.click();
  241 |         await this.page.waitForTimeout(2000);
  242 |         console.log(`✅ 切换到第 ${pageNumber} 页`);
  243 |       }
  244 |     }
  245 |   }
  246 | 
  247 |   async getToastMessage(): Promise<string | null> {
  248 |     const toast = this.page.locator('.el-message').first();
  249 |     if ((await toast.count()) > 0 && await toast.isVisible()) {
  250 |       const text = await toast.textContent();
  251 |       await this.page.waitForTimeout(1000);
  252 |       return text;
  253 |     }
  254 |     return null;
  255 |   }
  256 | 
  257 |   protected async waitForPageLoad(): Promise<void> {
  258 |     await this.page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  259 |     await this.page.waitForTimeout(2000);
  260 |   }
  261 | 
  262 |   protected async waitForVisible(locator: Locator, timeout: number = 10000): Promise<void> {
  263 |     await locator.waitFor({ state: 'visible', timeout });
  264 |   }
  265 | }
  266 | 
  267 | export class DialogBase extends BasePage {
  268 |   protected dialog: Locator;
  269 | 
> 270 |   constructor(page: Page, dialog: Locator) {
      |                 ^ TimeoutError: locator.waitFor: Timeout 10000ms exceeded.
  271 |     super(page);
  272 |     this.dialog = dialog;
  273 |   }
  274 | 
  275 |   async fillByPlaceholder(placeholder: string, value: string): Promise<void> {
  276 |     const input = this.dialog.locator(`input[placeholder="${placeholder}"]`);
  277 |     await input.waitFor({ state: 'visible', timeout: 10000 });
  278 |     await input.fill(value);
  279 |     console.log(`✅ 填写 [${placeholder}]: ${value}`);
  280 |   }
  281 | 
  282 |   async fillByLabel(labelText: string, value: string): Promise<void> {
  283 |     const formItem = this.dialog.locator('.el-form-item').filter({ hasText: labelText }).first();
  284 |     if ((await formItem.count()) > 0) {
  285 |       const input = formItem.locator('.el-input__inner, input').first();
  286 |       if ((await input.count()) > 0) {
  287 |         await input.waitFor({ state: 'visible', timeout: 10000 });
  288 |         await input.fill(value);
  289 |         console.log(`✅ 填写 [${labelText}]: ${value}`);
  290 |         return;
  291 |       }
  292 |     }
  293 | 
  294 |     const placeholderInput = this.dialog.locator(`input[placeholder*="${labelText}"]`).first();
  295 |     if ((await placeholderInput.count()) > 0) {
  296 |       await placeholderInput.waitFor({ state: 'visible', timeout: 10000 });
  297 |       await placeholderInput.fill(value);
  298 |       console.log(`✅ 通过占位符填写 [${labelText}]: ${value}`);
  299 |       return;
  300 |     }
  301 | 
  302 |     console.log(`⚠️ 未找到输入框 [${labelText}]`);
  303 |   }
  304 | 
  305 |   async selectByLabel(labelText: string, optionText: string): Promise<void> {
  306 |     await this.selectElOptionByLabel(labelText, optionText, this.dialog);
  307 |   }
  308 | 
  309 |   async submit(): Promise<void> {
  310 |     const submitPatterns = [/确定/, /提交/, /确\s*定/, /提\s*交/];
  311 | 
  312 |     for (const pattern of submitPatterns) {
  313 |       const button = this.dialog.locator('button').filter({ hasText: pattern }).first();
  314 |       if ((await button.count()) > 0 && await button.isVisible()) {
  315 |         await button.click({ force: true });
  316 |         console.log(`✅ 点击确定/提交按钮`);
  317 |         await this.page.waitForTimeout(2000);
  318 |         return;
  319 |       }
  320 |     }
  321 | 
  322 |     const pageButton = this.page.locator('button').filter({ hasText: /确定|提交/ }).first();
  323 |     if ((await pageButton.count()) > 0 && await pageButton.isVisible()) {
  324 |       await pageButton.click({ force: true });
  325 |       console.log(`✅ 通过页面定位点击确定/提交按钮`);
  326 |       await this.page.waitForTimeout(2000);
  327 |       return;
  328 |     }
  329 | 
  330 |     const primaryButton = this.page.locator('.el-button--primary').first();
  331 |     if ((await primaryButton.count()) > 0 && await primaryButton.isVisible()) {
  332 |       await primaryButton.click({ force: true });
  333 |       console.log(`✅ 通过样式类定位点击主按钮`);
  334 |       await this.page.waitForTimeout(2000);
  335 |       return;
  336 |     }
  337 | 
  338 |     console.log('⚠️ 未找到确定/提交按钮');
  339 |   }
  340 | 
  341 |   async close(): Promise<void> {
  342 |     const closePatterns = [/取消/, /关闭/, /取\s*消/, /关\s*闭/];
  343 | 
  344 |     for (const pattern of closePatterns) {
  345 |       const button = this.dialog.locator('button').filter({ hasText: pattern }).first();
  346 |       if ((await button.count()) > 0 && await button.isVisible()) {
  347 |         await button.click();
  348 |         console.log(`✅ 关闭弹窗`);
  349 |         return;
  350 |       }
  351 |     }
  352 | 
  353 |     const closeIcon = this.dialog.locator('.el-dialog__close, .el-drawer__close').first();
  354 |     if ((await closeIcon.count()) > 0 && await closeIcon.isVisible()) {
  355 |       await closeIcon.click();
  356 |       console.log(`✅ 点击关闭图标`);
  357 |       return;
  358 |     }
  359 | 
  360 |     console.log('⚠️ 未找到关闭按钮');
  361 |   }
  362 | }
```