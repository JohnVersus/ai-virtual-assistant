# src/core/dspy_handler.py
import dspy
from dspy.streaming import StreamResponse
from ..config.settings import load_settings
import asyncio
import subprocess
import sys
import os
import threading
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- Define a ReAct Signature for tool use ---
class ExecuteTaskWithTools(dspy.Signature):
    """
    Given a user request, understand the intent. If the intent matches a capability
    provided by one of the available tools, use the tool to accomplish the task.
    If no specific tool is needed for a general conversational query, respond directly.
    Always provide a final answer to the user, which might be a summary of the action taken by a tool
    or a direct conversational response.
    """
    user_request: str = dspy.InputField(desc="The user's request or question.")
    answer: str = dspy.OutputField(desc="The assistant's final response to the user, or a summary of the action taken by a tool.")

class GenerateResponse(dspy.Signature):
    """Generate a helpful and friendly response based on the conversation history."""
    history: list[dict] = dspy.InputField(desc="The conversation history, with roles 'user' and 'assistant'.")
    answer: str = dspy.OutputField(desc="The assistant's response.")

class DspyHandler:
    def __init__(self):
        self.settings = load_settings()
        self.lm = self._setup_dspy_lm() # LM setup is independent of MCP servers
        
        self.active_mcp_servers = [] # List to store Popen objects for stdio servers
        self.active_mcp_sessions = [] # List to store ClientSessionContextManagers

        self.dspy_tools = []
        self.react_agent = None
        self.fallback_predictor = None
        self.fallback_stream_predictor = None

        self._initialize_mcp_and_agent()

    def _get_mcp_server_script_path(self):
        """Determines the path to the mcp_tools_server.py script."""
        # For PyInstaller, sys._MEIPASS is the temp folder where bundled files are
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Expect mcp_tools_server.py at the root of the bundle
            return os.path.join(sys._MEIPASS, 'mcp_tools_server.py')
        else: # Running as a normal script
            # Correct path assuming dspy_handler.py and mcp_tools_server.py are in the same directory
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mcp_tools_server.py')

    def _start_mcp_server(self, command_list: list, env_vars: dict = None):
        """Starts an MCP server using the provided command list and optional environment variables."""
        # This method will now return the Popen object or None
        
        # For local Python script, ensure the first element (python executable) is valid
        # For external commands, command_list[0] is the command itself.
        if command_list[0] == sys.executable and not os.path.exists(command_list[1]):
             print(f"Error: MCP server script not found at {command_list[1]}")
             return False
        elif command_list[0] != sys.executable: # Check if external command exists (basic check)
            pass # More robust check might involve shutil.which(command_list[0])

        print(f"Attempting to start MCP server with command: {' '.join(command_list)}")
        
        current_env = os.environ.copy()
        if env_vars:
            current_env.update(env_vars)

        try:
            mcp_server_process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                close_fds=sys.platform != "win32",
                env=current_env
            )
            print(f"MCP server process starting with PID: {mcp_server_process.pid} for command: {' '.join(command_list)}")
            # Log MCP server output for debugging
            threading.Thread(target=self._log_subprocess_output, args=(mcp_server_process.stdout, f"MCP_OUT_{mcp_server_process.pid}"), daemon=True).start()
            threading.Thread(target=self._log_subprocess_output, args=(mcp_server_process.stderr, f"MCP_ERR_{mcp_server_process.pid}"), daemon=True).start()

            time.sleep(3) # Give server a moment to start
            if mcp_server_process.poll() is not None: # Check if process terminated prematurely
                print(f"MCP server for {' '.join(command_list)} failed to stay running. Exit code: {mcp_server_process.returncode}")
                # Attempt to read stderr for more clues
                # err_output = self.mcp_server_process.stderr.read() if self.mcp_server_process.stderr else "N/A"
                # print(f"MCP Server stderr: {err_output}")
                # raise RuntimeError(f"MCP server failed to stay running. Exit code: {mcp_server_process.returncode}") # Don't raise, just return None
                return None
            print(f"MCP server for {' '.join(command_list)} assumed to be running.")
            return mcp_server_process
        except Exception as e:
            print(f"Failed to start MCP server for {' '.join(command_list)}: {e}")
            return None

    def _log_subprocess_output(self, pipe, prefix):
        try:
            for line in iter(pipe.readline, ''):
                print(f"[{prefix}]: {line.strip()}")
        except ValueError: # Pipe closed
            pass
        except Exception as e:
            print(f"Error reading from {prefix}: {e}")
        finally:
            if hasattr(pipe, 'close') and not pipe.closed:
                pipe.close()

    async def _initialize_tools_from_server(self, mcp_popen_process, server_id: str):
        """Initializes MCP client for a given server process, loads its tools."""
        if not mcp_popen_process or mcp_popen_process.poll() is not None:
            print(f"MCP server process for '{server_id}' not running. Cannot initialize tools.")
            return [], None

        server_params = StdioServerParameters(command_or_popen_obj=mcp_popen_process)
        session_manager = ClientSessionContextManager(server_params)
        session = await session_manager.get_session()

        if not session:
            print(f"Failed to establish MCP session for server '{server_id}'.")
            await session_manager.close_session() # Clean up client if session failed
            return [], None

        try:
            tool_list_response = await session.list_tools()
            dspy_tools = [dspy.Tool.from_mcp_tool(session, tool_spec) for tool_spec in tool_list_response.tools]
            print(f"Loaded {len(dspy_tools)} MCP tools from server '{server_id}'.")
            return dspy_tools, session_manager
        except Exception as e:
            print(f"Error listing or converting tools from server '{server_id}': {e}")
            await session_manager.close_session()
            return [], None

    def _initialize_mcp_and_agent(self):
        self.dspy_tools = []
        self.active_mcp_servers = []
        self.active_mcp_sessions = []

        mcp_server_configs = self.settings.get("mcp_servers", [])
        if not isinstance(mcp_server_configs, list):
            print("Warning: 'mcp_servers' in settings is not a list. No MCP servers will be loaded.")
            mcp_server_configs = []

        all_loaded_dspy_tools = []

        for config in mcp_server_configs:
            if not config.get("enabled", False):
                print(f"MCP Server '{config.get('id', 'Unknown')}' is disabled. Skipping.")
                continue

            server_type = config.get("type")
            server_id = config.get("id", "UnnamedServer")

            if server_type == "stdio":
                command = config.get("command")
                args = config.get("args", [])
                env = config.get("env")

                if command:
                    full_command = [command] + args
                    mcp_process = self._start_mcp_server(command_list=full_command, env_vars=env)
                    if mcp_process:
                        self.active_mcp_servers.append(mcp_process)
                        # Initialize tools and session for this server
                        # This part needs to be async, so we'll collect tools later or adapt
                        # For now, let's assume we can run this part of init in a way that blocks or uses event loop
                        
                        # Running async tool initialization:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            future = asyncio.run_coroutine_threadsafe(self._initialize_tools_from_server(mcp_process, server_id), loop)
                            tools_from_this_server, session_mgr = future.result(timeout=15)
                        else:
                            tools_from_this_server, session_mgr = loop.run_until_complete(self._initialize_tools_from_server(mcp_process, server_id))
                        
                        if tools_from_this_server and session_mgr:
                            all_loaded_dspy_tools.extend(tools_from_this_server)
                            self.active_mcp_sessions.append(session_mgr)
                else:
                    print(f"stdio MCP Server '{server_id}' is missing 'command'. Skipping.")
            
            elif server_type == "http":
                print(f"HTTP MCP Server '{server_id}' configuration found. HTTP tool loading is not yet fully implemented in this handler. Skipping.")
                # Placeholder for future HTTP MCP client logic and dspy.Tool wrapping
            
            else:
                print(f"Unknown MCP Server type '{server_type}' for server '{server_id}'. Skipping.")

        self.dspy_tools = all_loaded_dspy_tools

        if self.dspy_tools:
            self.react_agent = dspy.ReAct(ExecuteTaskWithTools, tools=self.dspy_tools, lm=self.lm)
            print(f"ReAct agent initialized with {len(self.dspy_tools)} total MCP tools from all active servers.")
        else:
            print("No MCP tools loaded from any server. ReAct agent will not have tools.")
            self._setup_fallback_predictor()

    def _setup_fallback_predictor(self):
        print("No MCP tools loaded or MCP server failed. Setting up fallback DSPy predictor.")
        self.fallback_predictor = dspy.Predict(GenerateResponse)
        return dspy_tools

    def _initialize_mcp_and_agent(self):
        server_started = False
        full_command = []

        # Prioritize UI-driven external Python server settings
        if self.settings.get('mcp_use_external_python_server', False):
            script_path = self.settings.get('mcp_external_python_script_path', '')
            if script_path and os.path.exists(script_path):
                print(f"UI Config: Using external Python MCP server: {script_path}")
                full_command = [sys.executable, script_path]
            else:
                print(f"UI Config Error: External Python MCP script path not found or not set: '{script_path}'. Falling back.")
        
        # Fallback to generic external or local if UI external not used/valid
        if not full_command:
            mcp_server_type = self.settings.get("mcp_server_type", "local")
            if mcp_server_type == "external":
                command = self.settings.get("mcp_external_command")
                args = self.settings.get("mcp_external_args", [])
                if command:
                    full_command = [command] + args
                else:
                    print("Advanced Config Error: MCP server type is 'external' but 'mcp_external_command' is not set. Falling back to local.")
            else:
                print("Config: Using local bundled MCP server.")
                mcp_script_path = self._get_mcp_server_script_path()
                full_command = [sys.executable, mcp_script_path]

        if full_command:
            server_started = self._start_mcp_server(command_list=full_command, env_vars=self.settings.get("mcp_external_env"))
        else: # Should not happen if logic is correct, but as a safeguard
            print("Error: No valid MCP server command determined. Cannot start MCP server.")

        if server_started:
            try:
                # Run async initialization in the existing event loop if available, or a new one.
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If called from a sync context but loop is running (e.g. from app thread)
                    # This is tricky. For simplicity, let's assume this init is called
                    # before the main app loop fully takes over or from a context that can block.
                    future = asyncio.run_coroutine_threadsafe(self._initialize_tools_async(), loop)
                    self.dspy_tools = future.result(timeout=10) # Wait for tools
                else:
                    self.dspy_tools = loop.run_until_complete(self._initialize_tools_async())

                if self.dspy_tools:
                    self.react_agent = dspy.ReAct(ExecuteTaskWithTools, tools=self.dspy_tools, lm=self.lm)
                    print("ReAct agent initialized with MCP tools.")
                else:
                    print("No MCP tools loaded. ReAct agent will not have tools.")
                    self._setup_fallback_predictor()
            except Exception as e:
                print(f"Error during MCP tool/ReAct initialization: {e}")
                self._setup_fallback_predictor()
        else:
            print("MCP server failed to start. Using fallback predictor.")
            self._setup_fallback_predictor()

    def _setup_fallback_predictor(self):
        print("No MCP tools loaded or MCP server failed. Setting up fallback DSPy predictor.")
        self.fallback_predictor = dspy.Predict(GenerateResponse)
        self.fallback_stream_predictor = dspy.streamify(
            self.fallback_predictor,
            stream_listeners=[dspy.streaming.StreamListener(signature_field_name="answer")],
        )

    def _setup_dspy_lm(self):
        """Initializes and configures the DSPy language model."""
        # self.settings is already loaded in __init__
        api_key = self.settings.get('GOOGLE_API_KEY')
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please set it in your environment variables or settings.")
        lm = dspy.LM(model='gemini/gemini-1.5-flash', api_key=api_key, max_tokens=4000) # Adjust model as needed
        dspy.configure(lm=lm)
        return lm

    async def get_streamed_response(self, history: list[dict]):
        """
        Calls the LM with conversation history and yields streamed response chunks.
        """
        if not history:
            yield "No history provided to DspyHandler."
            return

        user_request = history[-1]['content']

        if self.react_agent and self.dspy_tools:
            print(f"Using ReAct agent for request: {user_request}")
            # Note: ReAct with tools from multiple MCP servers.
            # The dspy.Tool objects created by from_mcp_tool hold a reference to their session.
            # So, ReAct should be able to call the correct server via the tool's session.
            try:
                prediction = await self.react_agent.acall(user_request=user_request)
                final_answer = prediction.answer
                # print(f"ReAct Trajectory: {prediction.trajectory}") # For debugging
                # Stream the final answer
                # Ensure final_answer is a string
                final_answer = str(final_answer) if final_answer is not None else "No answer from agent."
                for i in range(0, len(final_answer), 10): # Chunk for streaming effect
                    yield final_answer[i:i+10]
                    await asyncio.sleep(0.01)
            except Exception as e:
                print(f"Error during ReAct agent call: {e}")
                yield f"Error processing your request with tools: {str(e)}"
        elif self.fallback_stream_predictor:
            print(f"Using fallback stream predictor for request: {user_request}")
            output_stream = self.fallback_stream_predictor(history=history)
            async for item in output_stream:
                if isinstance(item, StreamResponse):
                    yield item.chunk
        else:
            yield "Error: No valid DSPy agent or predictor is configured."

    async def shutdown(self):
        """Shuts down the DspyHandler, including the MCP server and client session."""
        print("Shutting down DspyHandler...")
        
        for session_manager in self.active_mcp_sessions:
            if session_manager:
                await session_manager.close_session()
        self.active_mcp_sessions = []

        for mcp_server_proc in self.active_mcp_servers:
            if mcp_server_proc and mcp_server_proc.poll() is None:
                print(f"Terminating MCP server process PID: {mcp_server_proc.pid}...")
                mcp_server_proc.terminate()
                try:
                    mcp_server_proc.wait(timeout=5)
                    print(f"MCP server process PID: {mcp_server_proc.pid} terminated.")
                except subprocess.TimeoutExpired:
                    print(f"MCP server process PID: {mcp_server_proc.pid} did not terminate in time, killing.")
                    mcp_server_proc.kill()
                    mcp_server_proc.wait()
        self.active_mcp_servers = []

# Helper class to manage MCP ClientSession lifecycle for ReAct
class ClientSessionContextManager:
    def __init__(self, server_params: StdioServerParameters):
        self.server_params = server_params
        self._client_cm = None
        self._read_pipe = None
        self._write_pipe = None
        self._session_cm = None
        self.session = None

    async def get_session(self):
        if self.session and await self.is_active(): # Simplistic check
            return self.session
        
        self._client_cm = stdio_client(self.server_params)
        self._read_pipe, self._write_pipe = await self._client_cm.__aenter__()

        self._session_cm = ClientSession(self._read_pipe, self._write_pipe)
        self.session = await self._session_cm.__aenter__()
        await self.session.initialize()
        return self.session

    async def is_active(self):
        # A more robust check would involve a ping or status check with the MCP server
        return self.session is not None # and self.server_params.command_or_popen_obj.poll() is None

    async def close_session(self):
        if self._session_cm:
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception as e:
                print(f"Error closing MCP session: {e}")
            self.session = None
            self._session_cm = None
        if self._client_cm:
            try:
                await self._client_cm.__aexit__(None, None, None)
            except Exception as e:
                print(f"Error closing MCP client: {e}")
            self._read_pipe = None
            self._write_pipe = None
            self._client_cm = None