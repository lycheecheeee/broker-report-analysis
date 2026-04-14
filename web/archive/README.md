# Archive - 舊版 HTML 文件歸檔

**歸檔日期**: 2026-04-14  
**說明**: 此文件夾包含已棄用或替換的舊版 HTML 文件，僅供參考和歷史追溯。

---

## 📁 文件清單

### 儀表板相關
- `broker_dashboard_old.html` - 舊版券商儀表板（已被 universal_pdf_dashboard.html 取代）
- `broker_dashboard_v2_old.html` - 券商儀表板 v2（過渡版本）
- `tencent_performance_dashboard_old.html` - 騰訊績效儀表板（獨立版本）

### 通用 PDF 儀表板
- `universal_pdf_dashboard_v2_old.html` - 通用 PDF 儀表板 v2（測試版本）

### 測試文件
- `test_login_old.html` - 登入系統測試頁面
- `test_system_old.html` - 系統功能測試頁面
- `auto_diagnosis_old.html` - 自動診斷頁面（空文件）
- `dashboard_old.html` - 基礎儀表板（空文件）

### 智能分析圖表
- `charts/` - 評級分佈圖表（5個PNG文件，生成於2026-04-09）
  - `rating_20260409_162707.png` - 評級餅圖 v1 (13.5KB)
  - `rating_20260409_162719.png` - 評級餅圖 v2 (13.5KB)
  - `rating_20260409_162733.png` - 評級餅圖 v3 (13.4KB)
  - `rating_20260409_174853.png` - 評級餅圖 v4 (11.7KB)
  - `rating_20260409_181232.png` - 評級餅圖 v5 (11.7KB)

---

## 🎯 當前使用文件

目前生產環境使用的是：
- ✅ `universal_pdf_dashboard.html` - 主儀表板（最新版本）
- ✅ `login.html` - 登入頁面
- ✅ `favicon.ico` - 網站圖標

---

## 📝 注意事項

1. **不要修改**：此文件夾中的文件僅供參考，不應再進行修改
2. **歷史追溯**：如需查看某個功能的演變歷史，可參考這些文件
3. **定期清理**：建議每季度審查一次，刪除完全無用的文件
4. **版本對比**：可使用 diff 工具對比新舊版本的差異

---

## 🔄 歸檔流程

當有新版本 HTML 文件時：
1. 將舊版本移動到此文件夾
2. 添加 `_old` 後綴以區分
3. 更新此 README 的文件清單
4. 確認新版本正常工作後再刪除舊版本（可選）

---

**最後更新**: 2026-04-14  
**維護者**: AI Assistant
