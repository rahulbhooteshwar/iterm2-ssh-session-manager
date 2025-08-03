#!/usr/bin/env python3
"""
A Gradio-based web UI for managing and launching SSH sessions
Enhanced version with better PyInstaller compatibility
"""

import gradio as gr
import json
import os
import subprocess
import sys
from pathlib import Path

# Setup for PyInstaller bundled applications
def setup_bundled_environment():
    """Setup environment for PyInstaller bundled applications"""
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        base_path = Path(sys._MEIPASS)

        # Set environment variables for Gradio
        os.environ.setdefault('GRADIO_FRONTEND_PATH', str(base_path / 'gradio' / 'frontend'))
        os.environ.setdefault('GRADIO_TEMPLATES_PATH', str(base_path / 'gradio' / 'templates'))
        os.environ.setdefault('GRADIO_THEMES_PATH', str(base_path / 'gradio' / 'themes'))
        os.environ.setdefault('GRADIO_ASSETS_PATH', str(base_path / 'gradio' / 'assets'))

        # Ensure Gradio can find its assets
        try:
            import gradio.utils
            original_get_asset_path = gradio.utils.get_asset_path

            def patched_get_asset_path(asset_name):
                """Patched version that handles bundled assets"""
                try:
                    return original_get_asset_path(asset_name)
                except (FileNotFoundError, OSError):
                    # Try alternative paths in bundled environment
                    for search_path in ['frontend', 'templates', 'themes', 'assets']:
                        alt_path = base_path / 'gradio' / search_path / asset_name
                        if alt_path.exists():
                            return str(alt_path)
                    raise

            gradio.utils.get_asset_path = patched_get_asset_path
        except (ImportError, AttributeError):
            pass

# Call setup function
setup_bundled_environment()

class WebSSHManager:
    def __init__(self, config_file="~/.ssh_manager_config.json"):
        self.config_file = os.path.expanduser(config_file)
        self.all_hosts = []
        self.refresh_hosts_data()

    def refresh_hosts_data(self):
        """Refresh hosts data from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.all_hosts = data.get('hosts', [])
            else:
                self.all_hosts = []
        except Exception as e:
            print(f"Error loading config: {e}")
            self.all_hosts = []

    def get_hosts_data(self, search_term=""):
        """Get filtered hosts data"""
        if not search_term:
            return self.all_hosts

        search_lower = search_term.lower()
        return [
            host for host in self.all_hosts
            if (search_lower in host.get('name', '').lower() or
                search_lower in host.get('tags', '').lower() or
                search_lower in host.get('host', '').lower())
        ]

    def get_unique_tags(self):
        """Get unique tags from all hosts"""
        tags = set()
        for host in self.all_hosts:
            host_tags = host.get('tags', '').split(',')
            tags.update([tag.strip() for tag in host_tags if tag.strip()])
        return sorted(list(tags))

    def get_hosts_by_tag(self, tag_filter=""):
        """Get hosts filtered by tag"""
        if not tag_filter or tag_filter == "All Tags":
            return self.all_hosts

        return [
            host for host in self.all_hosts
            if tag_filter.lower() in host.get('tags', '').lower()
        ]

    def create_clickable_tiles_html(self, search_term="", tag_filter=""):
        """Create HTML for clickable host tiles"""
        if tag_filter and tag_filter != "All Tags":
            hosts = self.get_hosts_by_tag(tag_filter)
        else:
            hosts = self.get_hosts_data(search_term)

        if not hosts:
            return """
            <div style="text-align: center; padding: 40px; color: #666;">
                <h3>🔍 No hosts found</h3>
                <p>Try adjusting your search or add some hosts first.</p>
                <p><em>Run <code>launch --add</code> in terminal to add hosts</em></p>
            </div>
            """

        tiles_html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; padding: 20px 0;">'

        for host in hosts:
            name = host.get('name', 'Unnamed')
            host_addr = host.get('host', '')
            user = host.get('user', '')
            port = host.get('port', '22')
            tags = host.get('tags', '')
            auth_type = host.get('auth_type', 'password')
            iterm_profile = host.get('iterm_profile', 'Default')

            # Determine auth icon and color
            if auth_type == 'key':
                auth_icon = "🔑"
                auth_color = "#28a745"
            else:
                auth_icon = "🔐"
                auth_color = "#007bff"

            # Create tag badges
            tag_badges = ""
            if tags:
                for tag in tags.split(','):
                    tag = tag.strip()
                    if tag:
                        tag_badges += f'<span style="background: {auth_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 5px;">{tag}</span>'

            tiles_html += f"""
            <div class="host-tile"
                 onclick="connectToHost('{name}')"
                 style="
                    background: white;
                    border: 2px solid #e9ecef;
                    border-radius: 15px;
                    padding: 20px;
                    cursor: pointer;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                 "
                 onmouseover="this.style.borderColor='{auth_color}'; this.style.transform='translateY(-5px)'; this.style.boxShadow='0 8px 25px rgba(0,0,0,0.15)'"
                 onmouseout="this.style.borderColor='#e9ecef'; this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)'">

                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: #333; font-size: 18px; font-weight: 600;">{name}</h3>
                    <span style="font-size: 20px;">{auth_icon}</span>
                </div>

                <div style="margin-bottom: 15px;">
                    <p style="margin: 5px 0; color: #666; font-size: 14px;">
                        <strong>Host:</strong> {host_addr}
                    </p>
                    <p style="margin: 5px 0; color: #666; font-size: 14px;">
                        <strong>User:</strong> {user}
                    </p>
                    <p style="margin: 5px 0; color: #666; font-size: 14px;">
                        <strong>Port:</strong> {port}
                    </p>
                    <p style="margin: 5px 0; color: #666; font-size: 14px;">
                        <strong>Profile:</strong> {iterm_profile}
                    </p>
                </div>

                <div style="margin-bottom: 15px;">
                    {tag_badges}
                </div>

                <div style="
                    background: linear-gradient(135deg, {auth_color}15, {auth_color}25);
                    padding: 10px;
                    border-radius: 8px;
                    text-align: center;
                    color: {auth_color};
                    font-weight: 600;
                    font-size: 14px;
                ">
                    ✨ Click to connect
                </div>
            </div>
            """

        tiles_html += '</div>'
        return tiles_html

    def connect_to_host_by_name(self, host_name):
        """Connect to a host by name"""
        try:
            # Find the host
            host = None
            for h in self.all_hosts:
                if h.get('name') == host_name:
                    host = h
                    break

            if not host:
                return f"❌ **Host not found**\n\nHost '{host_name}' not found in configuration."

            def launch_session():
                try:
                    # Build the iTerm2 command
                    cmd = [
                        'osascript', '-e',
                        f'tell application "iTerm2" to create window with default profile command "ssh -p {host.get("port", "22")} {host.get("user", "")}@{host.get("host", "")}"'
                    ]

                    # Execute the command
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

                    if result.returncode == 0:
                        return f"✅ **Connected successfully!**\n\n*Session opened with **{host.get('iterm_profile', 'Default')}** profile*"
                    else:
                        return f"❌ **Connection failed**\n\nError: {result.stderr}"

                except subprocess.TimeoutExpired:
                    return "❌ **Connection timeout**\n\nPlease check your network connection and try again."
                except Exception as e:
                    return f"❌ **Connection Error**\n\n{str(e)}"

            return launch_session()

        except Exception as e:
            return f"❌ **Connection Error**\n\n{str(e)}"

    def create_interface(self):
        """Create the Gradio interface with enhanced error handling"""
        try:
            with gr.Blocks(
                title="SSH Session Manager",
                theme=gr.themes.Soft(),
                css="""
                .gradio-container {
                    max-width: 1600px !important;
                    margin: 0 auto;
                }
                .host-tile {
                    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
                }
                .host-tile:hover {
                    transform: translateY(-8px) scale(1.02) !important;
                }
                .hidden-selector {
                    position: absolute !important;
                    left: -9999px !important;
                    opacity: 0 !important;
                    pointer-events: none !important;
                    height: 1px !important;
                    width: 1px !important;
                    overflow: hidden !important;
                }
                .footer-text {
                    text-align: center;
                    opacity: 0.8;
                    font-size: 14px;
                    margin-top: 20px;
                }
                """
            ) as interface:

                # Compact header section
                def create_header_info():
                    total_hosts = len(self.all_hosts)
                    return f"""
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 15px 25px;
                        border-radius: 12px;
                        margin-bottom: 20px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                    ">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <h2 style="margin: 0; font-size: 24px; font-weight: 700;">🖥️ SSH Session Manager</h2>
                            <span style="background: rgba(255,255,255,0.2); padding: 5px 12px; border-radius: 20px; font-size: 14px;">
                                {total_hosts} hosts
                            </span>
                        </div>
                        <div style="font-size: 14px; opacity: 0.9;">
                            🔑 = SSH Key Auth • 🔐 = Password Auth • ✨ Click any tile to connect
                        </div>
                    </div>
                    """

                header_display = gr.HTML(value=create_header_info())

                # Search and controls
                with gr.Row():
                    search_box = gr.Textbox(
                        placeholder="🔍 Search hosts by name or tags...",
                        label="",
                        scale=3,
                        show_label=False
                    )
                    tag_filter_dropdown = gr.Dropdown(
                        choices=["All Tags"] + self.get_unique_tags(),
                        value="All Tags",
                        label="Filter by Tag",
                        scale=2,
                        show_label=False
                    )

                # Main content area - full width for hosts
                hosts_display = gr.HTML(
                    value=self.create_clickable_tiles_html("", ""),
                    label="",
                    show_label=False
                )

                # Communication textbox (visible but styled to be invisible)
                with gr.Row():
                    hidden_host_selector = gr.Textbox(
                        label="",
                        elem_id="hidden-host-selector",
                        interactive=True,
                        show_label=False,
                        container=False,
                        elem_classes=["hidden-selector"]
                    )

                # Status display
                status_display = gr.Markdown(
                    value="Ready to connect! Click any host tile above.",
                    label="Status"
                )

                # Set up the JavaScript function using Gradio's JS integration
                interface.load(
                    None,
                    None,
                    None,
                    js="""
                    function() {
                        console.log("Setting up connectToHost function...");

                        // Define the global connectToHost function
                        window.connectToHost = function(hostName) {
                            console.log("Connecting to host:", hostName);

                            // Try multiple methods to find and trigger the hidden input
                            let found = false;

                            // Method 1: Try to find by ID
                            let hiddenInput = document.querySelector('#hidden-host-selector input, #hidden-host-selector textarea');
                            if (hiddenInput) {
                                console.log("Found hidden input by ID");
                                hiddenInput.value = hostName;
                                hiddenInput.dispatchEvent(new Event('input', { bubbles: true }));
                                hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
                                found = true;
                            }

                            // Method 2: Find any text input or textarea if Method 1 failed
                            if (!found) {
                                const inputs = document.querySelectorAll('input[type="text"], textarea');
                                console.log("Found", inputs.length, "text inputs/textareas total");

                                for (let input of inputs) {
                                    const isHidden = input.style.display === 'none' ||
                                                   input.hasAttribute('hidden') ||
                                                   input.parentElement.style.display === 'none' ||
                                                   input.offsetParent === null ||
                                                   input.closest('[style*="display: none"]') !== null;

                                    console.log("Checking input:", input, "isHidden:", isHidden);

                                    if (isHidden || input.closest('#hidden-host-selector') || input.getAttribute('data-testid') === 'hidden-host-selector') {
                                        console.log("Found communication input, setting value:", hostName);
                                        input.value = hostName;

                                        // Trigger multiple events
                                        input.dispatchEvent(new Event('input', { bubbles: true }));
                                        input.dispatchEvent(new Event('change', { bubbles: true }));
                                        input.dispatchEvent(new Event('blur', { bubbles: true }));

                                        // Force focus and blur to ensure Gradio detects the change
                                        input.focus();
                                        input.blur();

                                        found = true;
                                        break;
                                    }
                                }
                            }

                            if (!found) {
                                console.error("Could not find hidden input for host connection");
                            }
                        };

                        console.log("connectToHost function ready!");
                        return "JavaScript initialized";
                    }
                    """
                )

                with gr.Row():
                    gr.Markdown("""
                    **💡 Quick Guide:** Click any tile to connect instantly! Use search to filter hosts. Need to add hosts? Run `launch --add` in terminal.

                    **Built with ❤️ by RB (Rahul Bhooteshwar)**
                    """, elem_classes=["footer-text"])

                # Event handlers
                def update_display_by_search(search_term=""):
                    # Clear tag filter when searching
                    return self.create_clickable_tiles_html(search_term, "All Tags"), "All Tags"

                def update_display_by_tag(tag_filter="All Tags"):
                    # Clear search when filtering by tag
                    return self.create_clickable_tiles_html("", tag_filter), ""

                def handle_host_selection(host_name):
                    if host_name:
                        result = self.connect_to_host_by_name(host_name)
                        return result
                    return "Ready to connect! Click any host tile above."

                # Connect events
                search_box.change(
                    update_display_by_search,
                    inputs=[search_box],
                    outputs=[hosts_display, tag_filter_dropdown]
                )

                tag_filter_dropdown.change(
                    update_display_by_tag,
                    inputs=[tag_filter_dropdown],
                    outputs=[hosts_display, search_box]
                )

                hidden_host_selector.change(
                    handle_host_selection,
                    inputs=[hidden_host_selector],
                    outputs=[status_display]
                )

            return interface

        except Exception as e:
            # Fallback interface if Gradio fails to load properly
            print(f"Error creating Gradio interface: {e}")
            with gr.Blocks(title="SSH Session Manager - Fallback") as interface:
                gr.Markdown(f"""
                # SSH Session Manager

                **Error loading interface:** {str(e)}

                This might be due to missing frontend assets in the bundled application.
                Please restart the application or contact support.

                **Config file:** {self.config_file}
                **Total hosts:** {len(self.all_hosts)}
                """)
            return interface


def launch_web_interface(config_file="~/.ssh_manager_config.json", share=False, port=7860, silent=False):
    """Launch the web interface with enhanced error handling"""
    try:
        if not silent:
            print("🌐 Starting SSH Session Manager Web Interface...")
            print(f"📁 Using config: {config_file}")

        web_manager = WebSSHManager(config_file)
        interface = web_manager.create_interface()

        if not silent:
            print(f"🚀 Launching on http://localhost:{port}")
            if share:
                print("🔗 Creating shareable link...")

        # Enhanced launch with better error handling
        interface.launch(
            server_port=port,
            share=share,
            show_error=not silent,  # Suppress errors in silent mode
            inbrowser=not silent,   # Don't open browser in silent mode
            quiet=silent,           # Suppress Gradio output in silent mode
            prevent_thread_lock=True,  # Prevent thread locking issues
            show_api=False,         # Disable API docs to reduce complexity
        )

    except Exception as e:
        print(f"❌ Failed to launch web interface: {e}")
        if not silent:
            print("💡 Try restarting the application or check if the port is available.")
        raise


if __name__ == "__main__":
    launch_web_interface()