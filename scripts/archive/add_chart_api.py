import sqlite3
import json
from datetime import datetime

# Add chart generation API to backend
chart_api_code = '''

@app.route('/broker_3quilm/api/charts', methods=['GET'])
@token_required
def get_charts(current_user):
    """Generate analytical charts for broker reports"""
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Get all analysis results for current user
        c.execute('''SELECT broker_name, rating, target_price, current_price, upside_potential, created_at 
                     FROM analysis_results WHERE user_id=? ORDER BY created_at DESC''', (current_user['id'],))
        results = c.fetchall()
        conn.close()
        
        if not results:
            return jsonify({'error': 'No data available for charts'}), 404
        
        # Prepare data for charts
        brokers = []
        ratings = []
        target_prices = []
        current_prices = []
        upsides = []
        dates = []
        
        for row in results:
            brokers.append(row[0] or 'Unknown')
            ratings.append(row[1] or 'N/A')
            target_prices.append(row[2] if row[2] else 0)
            current_prices.append(row[3] if row[3] else 0)
            upsides.append(row[4] if row[4] else 0)
            dates.append(row[5][:10] if row[5] else '')
        
        # Calculate statistics
        avg_upside = sum(upsides) / len(upsides) if upsides else 0
        buy_count = ratings.count('Buy')
        hold_count = ratings.count('Hold')
        sell_count = ratings.count('Sell')
        
        charts_data = {
            'summary': {
                'total_reports': len(results),
                'avg_upside_potential': round(avg_upside, 2),
                'rating_distribution': {
                    'Buy': buy_count,
                    'Hold': hold_count,
                    'Sell': sell_count
                }
            },
            'data': {
                'brokers': brokers[:10],  # Top 10
                'target_prices': target_prices[:10],
                'current_prices': current_prices[:10],
                'upsides': upsides[:10],
                'ratings': ratings[:10],
                'dates': dates[:10]
            }
        }
        
        return jsonify(charts_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
'''

# Read current backend
with open('backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add chart API before the main block
if '/api/charts' not in content:
    # Find the position before if __name__ == '__main__'
    insert_pos = content.find("if __name__ == '__main__':")
    if insert_pos > 0:
        content = content[:insert_pos] + chart_api_code + '\n' + content[insert_pos:]
        
        with open('backend.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('✓ Added charts API to backend')
    else:
        print('✗ Could not find insertion point')
else:
    print('Charts API already exists')
