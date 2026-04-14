# Simpler approach - just add the endpoint
chart_endpoint = """
@app.route('/broker_3quilm/api/charts', methods=['GET'])
@token_required
def get_charts(current_user):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT broker_name, rating, target_price, current_price, upside_potential FROM analysis_results WHERE user_id=? ORDER BY created_at DESC LIMIT 10', (current_user['id'],))
        results = c.fetchall()
        conn.close()
        
        brokers = [r[0] or 'Unknown' for r in results]
        ratings = [r[1] or 'N/A' for r in results]
        upsides = [r[4] if r[4] else 0 for r in results]
        
        buy_count = ratings.count('Buy')
        hold_count = ratings.count('Hold')
        sell_count = ratings.count('Sell')
        
        return jsonify({
            'brokers': brokers,
            'ratings': ratings,
            'upsides': upsides,
            'distribution': {'Buy': buy_count, 'Hold': hold_count, 'Sell': sell_count}
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

"""

with open('backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

if '/api/charts' not in content:
    insert_pos = content.find("if __name__ == '__main__':")
    if insert_pos > 0:
        content = content[:insert_pos] + chart_endpoint + content[insert_pos:]
        with open('backend.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('✓ Charts API added successfully')
else:
    print('Charts API already exists')
