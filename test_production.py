#!/usr/bin/env python3
"""Test Production Deployment - Chart Data & Export Analysis"""
import requests
import json

BASE_URL = "https://broker-report-analysis.vercel.app"

print("="*60)
print("PRODUCTION DEPLOYMENT TEST")
print("="*60)

# Test 1: Chart Data API
print("\n[Test 1] Testing Chart Data API...")
try:
    response = requests.get(
        f"{BASE_URL}/broker_3quilm/api/chart-data",
        timeout=15
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Chart Data API working!")
        print(f"   Keys: {list(data.keys())}")
        
        # Check market sentiment
        sentiment = data.get('market_sentiment', '')
        if sentiment:
            print(f"   Market Sentiment: {sentiment[:100]}...")
        
        # Check price statistics
        price_stats = data.get('price_statistics', {})
        print(f"   Total Reports: {price_stats.get('total_reports', 0)}")
        print(f"   Average Price: HK${price_stats.get('average_price', 0):.2f}")
        print(f"   Median Price: HK${price_stats.get('median_price', 0):.2f}")
        print(f"   Average Upside: {price_stats.get('average_upside', 0):.2f}%")
        print(f"   Bull/Bear/Neutral: {price_stats.get('bull_count', 0)}/{price_stats.get('bear_count', 0)}/{price_stats.get('neutral_count', 0)}")
        
        # Check broker coverage
        broker_coverage = data.get('broker_coverage', [])
        print(f"   Broker Coverage: {len(broker_coverage)} brokers")
        
        if broker_coverage:
            print(f"   Top Broker: {broker_coverage[0]['broker']} ({broker_coverage[0]['count']} reports)")
            if 'average_target_price' in broker_coverage[0]:
                print(f"   Avg Target Price: HK${broker_coverage[0]['average_target_price']:.2f}")
            if 'consensus_rating' in broker_coverage[0]:
                print(f"   Consensus: {broker_coverage[0]['consensus_rating']} ({broker_coverage[0]['consensus_ratio']}%)")
        
        # Check rating distribution
        rating_dist = data.get('rating_distribution', [])
        print(f"   Rating Distribution: {len(rating_dist)} ratings")
        
    else:
        print(f"❌ Chart Data API failed: HTTP {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)[:100]}")

# Test 2: Export Analysis API
print("\n[Test 2] Testing Export Analysis API...")
try:
    response = requests.get(
        f"{BASE_URL}/broker_3quilm/api/export-analysis",
        timeout=15
    )
    
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', 'N/A')
        content_length = response.headers.get('Content-Length', 'N/A')
        print(f"✅ Export Analysis successful!")
        print(f"   Content-Type: {content_type}")
        print(f"   File Size: {content_length} bytes")
    elif response.status_code == 404:
        error_data = response.json()
        print(f"⚠️  Export returned 404: {error_data.get('error', 'Unknown error')}")
    else:
        print(f"❌ Export failed: HTTP {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)[:100]}")

# Test 3: Get Results API
print("\n[Test 3] Testing Get Results API...")
try:
    response = requests.get(
        f"{BASE_URL}/broker_3quilm/api/results",
        timeout=10
    )
    
    if response.status_code == 200:
        results = response.json()
        count = len(results) if isinstance(results, list) else 0
        print(f"✅ Get Results successful!")
        print(f"   Total Records: {count}")
        
        if count > 0:
            latest = results[0]
            print(f"   Latest Record:")
            print(f"     - File: {latest.get('pdf_filename', 'N/A')}")
            print(f"     - Broker: {latest.get('broker_name', 'N/A')}")
            print(f"     - Rating: {latest.get('rating', 'N/A')}")
            print(f"     - Target Price: HK${latest.get('target_price', 'N/A')}")
    else:
        print(f"❌ Get Results failed: HTTP {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)[:100]}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
