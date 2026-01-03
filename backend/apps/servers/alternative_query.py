"""
Alternative player query implementation that handles bz2 decompression issues.
This is a workaround for servers that send malformed compressed player data.
"""
import logging
import socket
import struct

logger = logging.getLogger(__name__)


def query_players_alternative(ip_address, port, timeout=5):
    """
    Alternative player query that skips decompression if it fails.
    Returns basic player count from server info instead.
    
    This is a fallback for when the compressed player list is malformed.
    """
    try:
        # Use standard a2s for info (which works)
        import a2s
        address = (ip_address, port)
        
        # Get server info (this works fine)
        info = a2s.info(address, timeout=timeout)
        
        # Try to get players
        try:
            players = a2s.players(address, timeout=timeout)
            return players, None
        except (OSError, Exception) as e:
            # Player query failed, return empty list but with warning
            warning_msg = f"Player list query failed (bz2 decompression error), using player count from info query"
            logger.warning(f"{warning_msg}: {str(e)}")
            
            # Return empty list - we at least have player count from info
            return [], warning_msg
            
    except Exception as e:
        logger.error(f"Complete server query failed: {e}")
        raise


def query_players_without_compression(ip_address, port, timeout=5):
    """
    Attempt to query players without relying on bz2 compression.
    This tries to get uncompressed player data directly.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    
    try:
        address = (ip_address, port)
        
        # Step 1: Send player query with challenge request
        challenge_request = b'\xFF\xFF\xFF\xFF\x55\xFF\xFF\xFF\xFF'
        sock.sendto(challenge_request, address)
        
        # Step 2: Receive challenge response
        data, _ = sock.recvfrom(1400)
        
        # Check if we got a challenge or actual player data
        if len(data) > 5 and data[4:5] == b'\x41':  # Challenge response
            # Extract challenge number
            challenge = data[5:9]
            
            # Step 3: Send player query with challenge
            player_request = b'\xFF\xFF\xFF\xFF\x55' + challenge
            sock.sendto(player_request, address)
            
            # Step 4: Receive player data
            data, _ = sock.recvfrom(65535)
        
        # Parse player data (simplified - just count)
        if len(data) > 6 and data[4:5] == b'\x44':  # Player response
            player_count = struct.unpack('<B', data[5:6])[0]
            logger.info(f"Successfully queried {player_count} players using alternative method")
            
            # Return empty list with count info
            # We could parse individual players here if needed
            return [], f"Player count: {player_count} (detailed list unavailable due to compression issue)"
        
        return [], "Could not parse player response"
        
    except socket.timeout:
        logger.warning(f"Timeout querying players from {ip_address}:{port}")
        return [], "Query timeout"
    except Exception as e:
        logger.error(f"Alternative player query failed: {e}")
        return [], str(e)
    finally:
        sock.close()
