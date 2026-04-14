# Check if matplotlib and other charting libraries are available
try:
    import matplotlib
    print("✓ Matplotlib available")
except:
    print("✗ Matplotlib NOT available")

try:
    import plotly
    print("✓ Plotly available")
except:
    print("✗ Plotly NOT available")

try:
    import pandas
    print("✓ Pandas available")
except:
    print("✗ Pandas NOT available")

# Check backend.py for existing chart functionality
with open('backend.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
has_chart_route = '/api/chart' in content or 'chart' in content.lower()
print(f"\nBackend has chart API: {has_chart_route}")
