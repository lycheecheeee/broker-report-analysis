#!/usr/bin/env python3
"""
圖表生成問題診斷工具
測試 chart-data API 端點和前端渲染邏輯
"""
import requests
import json

BASE_URL = "https://broker-report-analysis.vercel.app"

def test_chart_data_api():
    """測試 chart-data API 端點"""
    print("=" * 80)
    print("測試 Chart Data API")
    print("=" * 80)
    
    url = f"{BASE_URL}/broker_3quilm/api/chart-data"
    print(f"\nURL: {url}\n")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API 返回成功！")
            print(f"\n返回數據結構:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 檢查各個字段
            print("\n" + "=" * 80)
            print("數據驗證:")
            print("=" * 80)
            
            # 1. Rating Distribution
            rating_dist = data.get('rating_distribution', [])
            print(f"\n1. 評級分佈 (rating_distribution):")
            print(f"   - 記錄數: {len(rating_dist)}")
            if rating_dist:
                for item in rating_dist[:5]:
                    print(f"     • {item['rating']}: {item['count']}")
            else:
                print(f"   ⚠️ 警告: 評級分佈為空！")
            
            # 2. Price Statistics
            price_stats = data.get('price_statistics', {})
            print(f"\n2. 目標價統計 (price_statistics):")
            print(f"   - 總報告數: {price_stats.get('total_reports', 0)}")
            print(f"   - 平均目標價: HK${price_stats.get('average_price', 0)}")
            print(f"   - 最低目標價: HK${price_stats.get('min_price', 0)}")
            print(f"   - 最高目標價: HK${price_stats.get('max_price', 0)}")
            
            if price_stats.get('total_reports', 0) == 0:
                print(f"   ⚠️ 警告: 沒有目標價數據！")
            
            # 3. Broker Coverage
            broker_cov = data.get('broker_coverage', [])
            print(f"\n3. 券商覆蓋 (broker_coverage):")
            print(f"   - 券商數量: {len(broker_cov)}")
            if broker_cov:
                for item in broker_cov[:5]:
                    print(f"     • {item['broker']}: {item['count']} 份報告")
            else:
                print(f"   ⚠️ 警告: 券商覆蓋數據為空！")
            
            # 4. Trend Data
            trend_data = data.get('trend_data', [])
            print(f"\n4. 時間趨勢 (trend_data):")
            print(f"   - 天數: {len(trend_data)}")
            if trend_data:
                for item in trend_data[:5]:
                    print(f"     • {item['date']}: {item['count']} 份")
            else:
                print(f"   ⚠️ 警告: 時間趨勢數據為空！")
            
            # 總結
            print("\n" + "=" * 80)
            print("診斷結論:")
            print("=" * 80)
            
            has_data = (
                len(rating_dist) > 0 or 
                price_stats.get('total_reports', 0) > 0 or
                len(broker_cov) > 0 or
                len(trend_data) > 0
            )
            
            if has_data:
                print("✅ Supabase 中有數據，API 正常返回")
                print("   → 問題可能在前端 JavaScript 或 Chart.js 載入")
            else:
                print("❌ Supabase 中沒有數據")
                print("   → 根本原因: PDF 分析結果未保存到 Supabase")
                print("   → 解決方法: 配置 Vercel 環境變數 (SUPABASE_URL, SUPABASE_KEY)")
                
        elif response.status_code == 404:
            print("\n❌ API 端點不存在 (404)")
            print("   → 檢查 backend.py 中的路由定義")
        else:
            print(f"\n❌ HTTP {response.status_code}")
            print(f"   響應內容: {response.text[:200]}")
            
    except Exception as e:
        print(f"\n❌ 請求失敗: {e}")
        import traceback
        traceback.print_exc()

def test_supabase_connection():
    """直接測試 Supabase 連接"""
    print("\n\n" + "=" * 80)
    print("測試 Supabase 直接連接")
    print("=" * 80)
    
    import os
    from dotenv import load_dotenv
    
    # 嘗試加載 .env 文件
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ 已加載 .env 文件")
    else:
        print(f"⚠️ .env 文件不存在: {env_path}")
        print("   → 請在項目根目錄創建 .env 文件並配置 SUPABASE_URL 和 SUPABASE_KEY")
        return
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("\n❌ 環境變數未配置")
        print(f"   SUPABASE_URL: {'已設置' if supabase_url else '未設置'}")
        print(f"   SUPABASE_KEY: {'已設置' if supabase_key else '未設置'}")
        print("\n   → 請在 .env 文件中添加:")
        print("      SUPABASE_URL=https://your-project.supabase.co")
        print("      SUPABASE_KEY=your-service-role-key")
        return
    
    print(f"\n✅ 環境變數已配置")
    print(f"   SUPABASE_URL: {supabase_url[:30]}...")
    print(f"   SUPABASE_KEY: {supabase_key[:10]}...")
    
    # 測試查詢
    url = f"{supabase_url}/rest/v1/analysis_results?select=*&limit=5"
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"\nSupabase 查詢狀態: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 查詢成功！返回 {len(data)} 條記錄")
            
            if data:
                print(f"\n示例數據:")
                print(json.dumps(data[0], indent=2, ensure_ascii=False))
            else:
                print(f"\n⚠️ 表中沒有數據")
                print("   → 需要先運行 PDF 分析並將結果保存到 Supabase")
        else:
            print(f"❌ 查詢失敗: {response.status_code}")
            print(f"   響應: {response.text[:200]}")
            
    except Exception as e:
        print(f"\n❌ Supabase 連接失敗: {e}")

if __name__ == '__main__':
    test_chart_data_api()
    test_supabase_connection()
    
    print("\n\n" + "=" * 80)
    print("下一步行動:")
    print("=" * 80)
    print("1. 如果 Supabase 無數據 → 配置環境變數並重新掃描 PDF")
    print("2. 如果 Supabase 有數據但圖表不顯示 → 檢查瀏覽器 Console 錯誤")
    print("3. 如果 Chart.js 未載入 → 檢查 CDN 連結或網絡連接")
