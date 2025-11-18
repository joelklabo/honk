"""IPC server for external control of Honk Notes (socket-based API)."""

import socket
import json
import asyncio
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .app import StreamingNotesApp


class NotesIPCServer:
    """IPC server for external control via sockets.
    
    Allows agents and external tools to control a running Notes instance
    via JSON commands over TCP sockets (localhost only for security).
    
    Protocol:
        - Client connects to localhost:port
        - Client sends JSON: {"action": "...", ...params...}
        - Server responds with JSON: {"success": bool, ...data...}
        - Connection closes after response
    """
    
    def __init__(self, app: "StreamingNotesApp", port: int = 12345):
        """Initialize IPC server.
        
        Args:
            app: The StreamingNotesApp instance to control
            port: TCP port to listen on (default 12345)
        """
        self.app = app
        self.port = port
        self.server: Optional[socket.socket] = None
        self.running = False
    
    async def start(self):
        """Start IPC server (async).
        
        Listens for connections and handles commands until stopped.
        """
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('localhost', self.port))
        self.server.listen(1)
        self.server.setblocking(False)
        self.running = True
        
        while self.running:
            try:
                conn, addr = await asyncio.get_event_loop().sock_accept(self.server)
                asyncio.create_task(self.handle_connection(conn))
            except Exception as e:
                if self.running:
                    # Log error but keep running
                    print(f"IPC error: {e}")
    
    async def handle_connection(self, conn: socket.socket):
        """Handle single client connection.
        
        Args:
            conn: Client socket connection
        """
        try:
            # Receive command
            data = await asyncio.get_event_loop().sock_recv(conn, 4096)
            command_str = data.decode('utf-8')
            
            # Process command
            response = await self.handle_command(command_str)
            
            # Send response
            response_json = json.dumps(response).encode('utf-8')
            await asyncio.get_event_loop().sock_sendall(conn, response_json)
        
        except Exception as e:
            # Send error response
            error_response = json.dumps({
                "success": False,
                "error": str(e)
            }).encode('utf-8')
            try:
                await asyncio.get_event_loop().sock_sendall(conn, error_response)
            except Exception:
                pass
        
        finally:
            conn.close()
    
    async def handle_command(self, command_str: str) -> dict:
        """Handle incoming command and return response.
        
        Args:
            command_str: JSON command string
        
        Returns:
            Response dict (will be JSON-encoded)
        """
        try:
            cmd = json.loads(command_str)
            action = cmd.get("action")
            
            if action == "get_buffer":
                # Get buffer content
                return {
                    "success": True,
                    "content": self.app.api.read_buffer(),
                    "dirty": getattr(self.app, 'is_dirty', False)
                }
            
            elif action == "set_buffer":
                # Set buffer content
                content = cmd.get("content", "")
                self.app.api.write_buffer(content)
                return {"success": True}
            
            elif action == "save":
                # Save file
                self.app.action_save()
                return {
                    "success": True,
                    "file": str(self.app.config.file_path)
                }
            
            elif action == "organize":
                # Trigger AI organization
                await self.app.action_organize_now()
                return {"success": True}
            
            elif action == "get_state":
                # Get editor state
                state = self.app.api.get_editor_state()
                return {
                    "success": True,
                    "state": {
                        "open": state.open,
                        "organizing": state.organizing,
                        "file": str(self.app.config.file_path) if self.app.config.file_path else None,
                        "dirty": getattr(self.app, 'is_dirty', False),
                        "idle_seconds": state.idle_seconds
                    }
                }
            
            elif action == "get_status":
                # Get operational status
                status = self.app.state_detector.get_status()
                return {
                    "success": True,
                    "status": status.value,
                    "ready": self.app.state_detector.is_ready(),
                    "blocking": self.app.state_detector.is_blocking()
                }
            
            elif action == "get_capabilities":
                # Get capabilities
                caps = self.app.state_detector.get_capabilities()
                return {
                    "success": True,
                    "capabilities": {
                        "supports_organization": caps.supports_organization,
                        "supports_auto_save": caps.supports_auto_save,
                        "supports_custom_prompts": caps.supports_custom_prompts,
                        "supports_streaming": caps.supports_streaming,
                        "supports_ipc": caps.supports_ipc,
                        "max_file_size_mb": caps.max_file_size_mb
                    }
                }
            
            elif action == "close":
                # Close editor
                self.running = False
                self.app.exit()
                return {"success": True}
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop(self):
        """Stop IPC server."""
        self.running = False
        if self.server:
            try:
                self.server.close()
            except Exception:
                pass
