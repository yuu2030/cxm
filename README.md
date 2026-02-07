# CxM Kaohsiung 票況監控（可 fork 範例）

這個專案會每分鐘檢查 tixcraft 三個售票頁面，只要偵測到指定區域（站區/看台各價位）**沒有顯示「售罄字樣」**，就會用 **LINE Notify** 推送通知到你的手機。

## 功能
- 監控連結：
  - https://tixcraft.com/ticket/area/26_cxm/21777
  - https://tixcraft.com/ticket/area/26_cxm/21671
  - https://tixcraft.com/ticket/area/26_cxm/21672
- 監控區域關鍵字：
  - 6880站區、6280站區
  - 6880/6280/5880/4880/3880 看台區
- 支援多種售罄字樣：`已售完 / 暫無票券 / 尚未開賣 / Sold out`
- 避免重複通知：使用快取紀錄上次已通知的結果

## 使用方式
1. **Fork** 本專案（或直接點右上角的「Use this template」建立新 Repo）
2. 到 LINE Notify（<https://notify-bot.line.me/my/>）建立 **個人權杖（Token）**
3. 在 GitHub Repo → `Settings → Secrets and variables → Actions` 新增：
   - **Name**：`LINE_TOKEN`
   - **Value**：你的 LINE 個人權杖
4. 到 `Actions` 分頁，啟用工作流程（若提示 Enable，請按一下）
5. 手動執行一次工作流程（Run workflow）驗證是否能送出通知

> GitHub Actions 的排程是 **UTC**。本專案設定「每分鐘」執行，不受時差影響。

## 自訂
- 新增/修改監控網址：編輯 `script.py` 的 `URLS`
- 新增/調整售罄字樣：編輯 `SELL_PATTERNS`
- 修改排程頻率：編輯 `.github/workflows/check.yml` 的 `cron`

## 免責聲明
- 請依站方使用條款與合理頻率使用本工具。  
- 本專案僅供學習與個人用途，風險自負。
