# Confluence I4.0 Projects 页面树 (2026-05-27)

来源: https://inside-docupedia.bosch.com/confluence/spaces/I40Projects/pages/1158297671/I4.0+Projects
获取方式: PowerShell Invoke-WebRequest + Edge --dump-dom

## 页面列表 (42 pages)

### Root
- RBCDLOI Home [ID: 1158291629]

### LOC / LOQ
- LOC [ID: 1158297669]
- LOC_Digitalization [ID: 7064407039]
- LOQ [ID: 1158297652]

### Projects & Systems (24)
- A3 - Dynamic milkrun for Empty container [1758076079]
- Auto Blue sheet [1268940950]
- Auto MBR [1258085139]
- Auto_Capacity_Simulation [2083603436]
- CMS System [1182840081]
- Camera Docking Mgt [1328189307]
- Customer Inventory Transparency by RTP [2080428085]
- Dashboard [1857103358]
- Digi@LOP [1645055851]
- Digital Dashboard [1211109361]
- EDI with WFAC Phase 2 [1563809851]
- EOP_Stock_Check_Tool [2491645906]
- I 4.0 System Architecture [1291723331]
- I4.0 Project Checklist [1242575098]
- I4.0 Projects [1158297671]
- IDM Implementation [2361736797]
- IES Overview [1211847744]
- QINP Call Off Automation [2386884500]
- RFID @ RBCD [1326410926]
- Repack System [1305399810]
- Smart SAP [1158291733]
- Smart Supply Chain (Make) [1250818944]
- Strategic Project list [1917657005]
- Tableau [1211109355]

### Support & Resources (14)
- Database [6164361738]
- I4.0 Project Handover Standard_draft [2272362467]
- LOG App Catalog [2227279422]
- LOG I4.0 Project Management process V2 [2566282543]
- LOG-BPS [1243840895]
- Learning Space [1186767681]
- Meeting Minutes Project Weekly Review [1346925608]
- New User story brain storming [2220546683]
- Process Landscape [1592396111]
- Process Landscape-Project [1718772372]
- RBCD LOG Blueprint [2211432043]
- Reference [1211109399]
- Resources [1287009333]
- Useful Links [1242575053]

## Confluence 访问技术细节

- 该实例 REST API 大部分端点返回 404，仅 `/confluence/rest/api/search?cql=...` 可用
- 页面树是 JS 动态加载的，必须用 Edge `--dump-dom` 获取
- 正确的 REST API 基础路径: `https://inside-docupedia.bosch.com/confluence/rest/api/`
- 空间搜索: `space = I40Projects AND type = page` 仅返回 1 个页面（索引不完整）
- 完整页面树需通过 HTML 解析 Edge 渲染结果获取
