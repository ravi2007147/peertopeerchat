#!/usr/bin/env python3
"""
Network Classes for Peer-to-Peer Communication
"""

import socket
import json
import threading
import asyncio
import websockets
import time
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

class PeerDiscovery(QThread):
    """Thread for discovering peers on LAN using UDP broadcast"""
    peer_found = pyqtSignal(str, str, str)  # ip, username, uuid
    peer_lost = pyqtSignal(str)  # ip
    port_error = pyqtSignal(str)  # error message
    
    def __init__(self, current_user_uuid, current_username, discovery_port=8080):
        super().__init__()
        self.current_user_uuid = current_user_uuid
        self.current_username = current_username
        self.discovery_port = discovery_port
        self.discovered_peers = {}
        self.running = True
        
    def run(self):
        """Start peer discovery"""
        print("🔍 Starting peer discovery...")
        
        # Start broadcasting in a separate thread
        broadcast_thread = threading.Thread(target=self.broadcast_presence, daemon=True)
        broadcast_thread.start()
        
        # Start listening for peers
        self.listen_for_peers()
        
    def broadcast_presence(self):
        """Broadcast our presence to the network"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        try:
            while self.running:
                message = {
                    "type": "peer_announcement",
                    "username": self.current_username,
                    "uuid": self.current_user_uuid,
                    "port": 8081,
                    "discovery_port": self.discovery_port
                }
                
                data = json.dumps(message).encode()
                sock.sendto(data, ('255.255.255.255', self.discovery_port))
                print(f"📡 Broadcast sent successfully to 255.255.255.255:{self.discovery_port}")
                time.sleep(5)  # Broadcast every 5 seconds
                
        except Exception as e:
            print(f"❌ Broadcast error: {e}")
        finally:
            sock.close()
    
    def listen_for_peers(self):
        """Listen for peer announcements"""
        print("👂 Starting listener...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind(('', self.discovery_port))
            print(f"✅ Listening for peers on port {self.discovery_port}")
        except OSError as e:
            print(f"❌ Could not bind port {self.discovery_port}: {e}")
            self.port_error.emit(f"Port {self.discovery_port} already in use.\n\n{e}")
            return
        
        sock.settimeout(1.0)
        try:
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    peer_info = json.loads(data.decode())
                    print(f"📥 Received from {addr}: {peer_info}")
                    
                    if peer_info['type'] == 'peer_announcement':
                        ip = addr[0]
                        username = peer_info['username']
                        peer_uuid = peer_info.get('uuid', 'unknown')
                        
                        if peer_uuid != self.current_user_uuid:
                            if ip not in self.discovered_peers:
                                self.discovered_peers[ip] = {'username': username, 'uuid': peer_uuid}
                                print(f"👋 Found peer: {username} ({ip}) UUID={peer_uuid}")
                                self.peer_found.emit(ip, username, peer_uuid)
                            else:
                                self.discovered_peers[ip].update({'username': username, 'uuid': peer_uuid})
                        else:
                            print("🚫 Ignored self-announcement")
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Listen error: {e}")
                    break
        finally:
            sock.close()
    
    def stop(self):
        """Stop discovery cleanly"""
        print("🛑 Stopping peer discovery...")
        self.running = False
        self.wait(500)

class WebSocketServer(QThread):
    """WebSocket server for peer-to-peer communication"""
    message_received = pyqtSignal(str, str, str)  # sender_ip, message_type, content
    port_error = pyqtSignal(str)  # port error message
    
    def __init__(self, port=8081):
        super().__init__()
        self.port = port
        self.clients = {}
        self.running = True
        self.server = None
        self.active_transfers = {}  # Store active file transfers
        
    async def handle_client(self, websocket, path):
        """Handle incoming WebSocket connections"""
        client_ip = websocket.remote_address[0]
        self.clients[client_ip] = websocket
        
        try:
            async for message in websocket:
                data = json.loads(message)
                
                # Handle different message types
                if data['type'] == 'file_chunk':
                    await self.handle_file_chunk(client_ip, data)
                else:
                    # Handle regular messages
                    self.message_received.emit(client_ip, data['type'], data['content'])
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if client_ip in self.clients:
                del self.clients[client_ip]
    
    async def handle_file_chunk(self, client_ip: str, data: dict):
        """Handle incoming file chunks"""
        import base64
        transfer_id = data['transfer_id']
        chunk_data = base64.b64decode(data['chunk_data'])
        chunk_index = data['chunk_index']
        total_chunks = data['total_chunks']
        filename = data['filename']
        
        # Initialize transfer if first chunk
        if transfer_id not in self.active_transfers:
            self.active_transfers[transfer_id] = {
                'filename': filename,
                'sender_ip': client_ip,
                'chunks': {},
                'total_chunks': total_chunks,
                'file_size': data['file_size']
            }
        
        # Store chunk
        self.active_transfers[transfer_id]['chunks'][chunk_index] = chunk_data
        
        # Check if all chunks received
        if len(self.active_transfers[transfer_id]['chunks']) == total_chunks:
            await self.complete_file_transfer(transfer_id)
    
    async def complete_file_transfer(self, transfer_id: str):
        """Complete file transfer by assembling chunks"""
        import os
        transfer = self.active_transfers[transfer_id]
        filename = transfer['filename']
        sender_ip = transfer['sender_ip']
        
        try:
            # Create downloads directory if it doesn't exist
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads", "PeerToPeerChat")
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Assemble file
            file_path = os.path.join(downloads_dir, filename)
            with open(file_path, 'wb') as f:
                for i in range(transfer['total_chunks']):
                    if i in transfer['chunks']:
                        f.write(transfer['chunks'][i])
            
            # Notify about completed file
            self.message_received.emit(sender_ip, 'file_completed', filename)
            print(f"✅ File transfer completed: {filename} from {sender_ip}")
            
        except Exception as e:
            print(f"❌ Error completing file transfer: {e}")
            self.message_received.emit(sender_ip, 'file_error', str(e))
        finally:
            # Clean up transfer
            del self.active_transfers[transfer_id]
                
    async def start_server(self):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(self.handle_client, "0.0.0.0", self.port)
            print(f"✅ WebSocket server started on port {self.port}")
            
            # Wait for server to be closed
            await self.server.wait_closed()
        except OSError as e:
            print(f"❌ Port {self.port} is already in use!")
            print(f"❌ Error: {e}")
            print(f"💡 Please close the application using port {self.port} and try again.")
            # Emit error signal to main window
            self.port_error.emit(f"Port {self.port} is already in use by another application.\n\nPlease close the application using this port and try again.")
            return
        
    def run(self):
        """Run the WebSocket server"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_server())
        except Exception as e:
            print(f"WebSocket server error: {e}")
        finally:
            print("WebSocket server stopped")
        
    def stop(self):
        """Stop the WebSocket server"""
        print("Stopping WebSocket server...")
        self.running = False
        if self.server:
            # Close all client connections
            for client in self.clients.values():
                try:
                    asyncio.create_task(client.close())
                except:
                    pass
            # Close the server
            try:
                asyncio.create_task(self.server.close())
            except:
                pass
            # Clear clients
            self.clients.clear()
        
    def send_message(self, target_ip: str, message_type: str, content: str):
        """Send message to specific peer"""
        if target_ip in self.clients:
            message = json.dumps({
                'type': message_type,
                'content': content,
                'timestamp': datetime.utcnow().isoformat()
            })
            asyncio.create_task(self.clients[target_ip].send(message))

