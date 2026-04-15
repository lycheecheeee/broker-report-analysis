"""
測試 AI 字段提取功能
驗證 generate_ai_summary_with_fields 是否能正確推斷所有字段
"""
import sys
import os

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import generate_ai_summary_with_fields

def test_ai_field_extraction():
    """測試 AI 字段提取和推斷能力"""
    
    print("=" * 80)
    print("測試 AI 字段提取與智能推斷功能")
    print("=" * 80)
    print()
    
    # 模擬 PDF 文本（簡化版）
    sample_text = """
    Tencent Holdings Ltd. (0700.HK)
    
    Investment Rating: BUY
    Target Price: HKD 600
    
    Key Points:
    - Strong growth in gaming segment
    - WeChat user base continues to expand
    - Cloud computing revenue increased by 30% YoY
    - Fintech services showing robust performance
    
    Risks:
    - Regulatory uncertainties in China
    - Competition in cloud market intensifying
    """
    
    # 測試用例 1: BOA-700.pdf（騰訊控股）
    print("📄 測試用例 1: BOA-700.pdf")
    print("-" * 80)
    
    try:
        ai_summary, extracted_fields = generate_ai_summary_with_fields(
            broker_name="美國銀行",
            rating="買入",
            target_price=600.0,
            text=sample_text,
            filename="BOA-700.pdf"
        )
        
        print("✅ AI 分析完成！")
        print()
        print("📊 提取的字段:")
        print(f"  • 發布日期: {extracted_fields.get('release_date', 'MISSING')}")
        print(f"  • 股票名稱: {extracted_fields.get('stock_name', 'MISSING')}")
        print(f"  • 行業分類: {extracted_fields.get('industry', 'MISSING')}")
        print(f"  • 子行業: {extracted_fields.get('sub_industry', 'MISSING')}")
        print(f"  • 相關指數: {extracted_fields.get('indexes', 'MISSING')}")
        print(f"  • 投資期限: {extracted_fields.get('investment_horizon', 'MISSING')}")
        print()
        print(f"🔍 推斷字段: {extracted_fields.get('inferred_fields', [])}")
        print(f"📈 置信度評分: {extracted_fields.get('confidence_scores', {})}")
        print()
        print("📝 AI 摘要（前 200 字符）:")
        print(ai_summary[:200] + "..." if len(ai_summary) > 200 else ai_summary)
        print()
        
        # 驗證結果
        validation_results = []
        
        # 檢查是否有缺失字段
        required_fields = ['release_date', 'stock_name', 'industry', 'sub_industry', 
                          'indexes', 'investment_horizon', 'ai_summary']
        
        for field in required_fields:
            value = extracted_fields.get(field, '')
            if value and value not in ['-', '', None]:
                validation_results.append(f"✅ {field}: 已填充")
            else:
                validation_results.append(f"❌ {field}: 缺失或為空")
        
        print("🔎 驗證結果:")
        for result in validation_results:
            print(f"  {result}")
        
        print()
        
        # 檢查是否仍有「AI分析服務暫時不可用」
        if "AI分析服務暫時不可用" in ai_summary:
            print("⚠️  警告: AI 摘要中仍包含「AI分析服務暫時不可用」標記")
        else:
            print("✅ AI 摘要正常，無降級標記")
        
        print()
        print("=" * 80)
        print("測試完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 測試失敗: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_ai_field_extraction()
