import sys
sys.path.append('src')

print("Testing direct publish_to_confluence function...")
try:
    from src.publish_to_confluence import BASE, USER, TOKEN, SPACE
    print(f"BASE: {BASE}")
    print(f"USER: {USER}")
    print(f"TOKEN: {'SET' if TOKEN else 'NOT SET'}")
    print(f"SPACE: {SPACE}")
    
    # Test what URL would be constructed
    print(f"Would use URL: {BASE}/wiki/rest/api/content")
    
except Exception as e:
    print(f"Error importing: {e}")
