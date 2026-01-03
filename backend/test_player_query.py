"""Test script to investigate player query decompression issues."""
import sys
import traceback

import a2s


def test_player_query_raw():
    """Test raw player query to understand the decompression issue."""
    address = ('193.243.190.23', 27015)
    
    print("=" * 60)
    print("Testing Player Query - Investigation")
    print("=" * 60)
    
    # Test 1: Try normal query with detailed error
    print("\n1. Attempting normal player query...")
    try:
        players = a2s.players(address, timeout=10)
        print(f"✓ SUCCESS: Retrieved {len(players)} players")
        return True
    except OSError as e:
        print(f"✗ OSError: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"✗ Other Error: {e}")
        traceback.print_exc()
    
    # Test 2: Check if it's a fragmented response issue
    print("\n2. Checking response fragmentation...")
    try:
        from a2s.a2s_sync import DatagramSocket
        conn = DatagramSocket(address, timeout=10)
        conn.connect()
        
        # Send player query with challenge
        request = b'\xFF\xFF\xFF\xFF\x55\xFF\xFF\xFF\xFF'
        conn.send(request)
        
        response = conn.recv()
        print(f"   Received {len(response)} bytes")
        print(f"   First 10 bytes (hex): {response[:10].hex()}")
        
        # Check if it's a fragmented packet
        header = response[:4]
        if header == b'\xFE\xFF\xFF\xFF':
            print("   ⚠ Response is FRAGMENTED (multi-packet)")
            # Read more details about fragmentation
            print(f"   Full header (20 bytes): {response[:20].hex()}")
        elif header == b'\xFF\xFF\xFF\xFF':
            print("   ✓ Response is single packet")
        else:
            print(f"   ? Unknown header: {header.hex()}")
        
        conn.close()
    except Exception as e:
        print(f"   Error during raw test: {e}")
    
    # Test 3: Try with increased timeout
    print("\n3. Trying with longer timeout (20s)...")
    try:
        players = a2s.players(address, timeout=20)
        print(f"✓ SUCCESS with longer timeout: {len(players)} players")
        return True
    except Exception as e:
        print(f"✗ Still failed: {type(e).__name__}: {e}")
    
    return False

if __name__ == '__main__':
    success = test_player_query_raw()
    sys.exit(0 if success else 1)
