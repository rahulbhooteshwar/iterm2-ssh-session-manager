#!/usr/bin/env python3
"""
Web Interface for SSH Session Manager
A Gradio-based web UI for managing and launching SSH sessions
"""

import gradio as gr
import json
from main import SSHManager
import threading
import time


class WebSSHManager:
    def __init__(self, config_file="~/.ssh_manager_config.json"):
        self.ssh_manager = SSHManager(config_file)
        self.all_hosts = []
        self.filtered_hosts = []
        self.current_filter = ""
        self.refresh_hosts_data()

    def refresh_hosts_data(self):
        """Refresh the hosts data from config"""
        self.all_hosts = self.ssh_manager.config.get('hosts', [])
        self.filtered_hosts = self.all_hosts.copy()

    def get_hosts_data(self, search_term=""):
        """Get hosts data filtered by search term"""
        if search_term.strip():
            hosts = self.ssh_manager.filter_hosts(search_term)
        else:
            hosts = self.all_hosts
        self.filtered_hosts = hosts
        self.current_filter = search_term
        return hosts

    def get_unique_tags(self):
        """Get all unique tags from hosts"""
        tags = set()
        for host in self.all_hosts:
            host_tags = host.get('tags', [])
            tags.update(host_tags)
        return sorted(list(tags))

    def get_hosts_by_tag(self, tag_filter=""):
        """Get hosts filtered by tag"""
        if not tag_filter or tag_filter == "All Tags":
            hosts = self.all_hosts
        else:
            hosts = [host for host in self.all_hosts if tag_filter in host.get('tags', [])]
        self.filtered_hosts = hosts
        self.current_filter = tag_filter
        return hosts

    def create_clickable_tiles_html(self, search_term="", tag_filter=""):
        """Create beautiful clickable tiles"""
        # If tag filter is provided, use it; otherwise use search term
        if tag_filter and tag_filter != "All Tags":
            hosts = self.get_hosts_by_tag(tag_filter)
        else:
            hosts = self.get_hosts_data(search_term)

        if not hosts:
            return f"""
            <div style="
                text-align: center;
                padding: 60px 20px;
                color: #6c757d;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 20px;
                border: 3px dashed #dee2e6;
                margin: 20px 0;
                box-shadow: inset 0 2px 10px rgba(0,0,0,0.05);
            ">
                <div style="font-size: 64px; margin-bottom: 20px; opacity: 0.7;">📭</div>
                <h3 style="margin-bottom: 15px; color: #495057; font-weight: 600;">No SSH Hosts Found</h3>
                <p style="margin-bottom: 20px; font-size: 16px;">
                    {'No hosts match your search criteria.' if search_term else 'No SSH hosts configured yet.'}
                </p>
                {'<p style="font-style: italic; color: #6c757d;"><em>Try a different search term or clear the search.</em></p>' if search_term else '<p style="font-style: italic; color: #6c757d;"><em>Add hosts using: <code style="background: #e9ecef; padding: 2px 6px; border-radius: 4px;">launch --add</code></em></p>'}
            </div>
            """

        # Group hosts by tags
        tag_groups = {}
        untagged_hosts = []

        for host in hosts:
            host_tags = host.get('tags', [])
            if not host_tags:
                untagged_hosts.append(host)
            else:
                primary_tag = host_tags[0]
                if primary_tag not in tag_groups:
                    tag_groups[primary_tag] = []
                tag_groups[primary_tag].append(host)

        # Enhanced color scheme for tags
        tag_colors = {
            'production': '#dc3545', 'prod': '#dc3545',
            'staging': '#fd7e14', 'stage': '#fd7e14',
            'development': '#198754', 'dev': '#198754',
            'testing': '#6f42c1', 'test': '#6f42c1',
            'database': '#0dcaf0', 'db': '#0dcaf0',
            'web': '#0d6efd', 'api': '#6610f2',
            'default': '#6c757d'
                }

        html = f"""
        <div style="padding: 15px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            {f'<div style="margin-bottom: 20px; text-align: center; padding: 10px; background: #e3f2fd; border-radius: 8px; color: #1565c0; font-weight: 500;">Filtered by: "{search_term}"</div>' if search_term else ''}
        """

        # Add tagged groups
        for tag in sorted(tag_groups.keys()):
            tag_color = tag_colors.get(tag.lower(), tag_colors['default'])

            html += f"""
            <div style="margin-bottom: 50px;">
                <h3 style="
                    color: {tag_color};
                    margin-bottom: 25px;
                    padding: 18px 30px;
                    background: linear-gradient(135deg, {tag_color}15 0%, {tag_color}08 100%);
                    border-left: 6px solid {tag_color};
                    border-radius: 0 15px 15px 0;
                    font-size: 22px;
                    font-weight: 700;
                    box-shadow: 0 4px 15px {tag_color}25;
                    letter-spacing: 1px;
                    text-transform: uppercase;
                ">
                    📁 {tag.upper()} ({len(tag_groups[tag])})
                </h3>
                <div style="
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 20px;
                    padding: 0 15px;
                ">
            """

            for host in tag_groups[tag]:
                auth_icon = "🔑" if host.get('auth_method') == 'key' else "🔐"
                tags_str = ", ".join(host.get('tags', []))

                html += f"""
                <div class="host-tile"
                     data-host-name="{host['name']}"
                     style="
                    background: linear-gradient(135deg, {tag_color}20 0%, {tag_color}35 100%);
                    border: 3px solid {tag_color}60;
                    border-radius: 12px;
                    padding: 15px 18px;
                    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    cursor: pointer;
                    position: relative;
                    box-shadow: 0 6px 20px {tag_color}30;
                    overflow: hidden;
                "
                onmouseover="
                    this.style.transform='translateY(-4px) scale(1.01)';
                    this.style.boxShadow='0 12px 30px {tag_color}50';
                    this.style.borderColor='{tag_color}80';
                "
                onmouseout="
                    this.style.transform='translateY(0) scale(1)';
                    this.style.boxShadow='0 6px 20px {tag_color}30';
                    this.style.borderColor='{tag_color}60';
                "
                onclick="window.connectToHost && window.connectToHost('{host['name']}')">

                    <!-- Host Name -->
                    <div style="
                        font-size: 18px;
                        font-weight: 700;
                        color: #ffffff;
                        margin-bottom: 10px;
                        text-align: center;
                        border-bottom: 2px solid {tag_color}60;
                        padding-bottom: 8px;
                        position: relative;
                        z-index: 1;
                        letter-spacing: 0.3px;
                        text-shadow: 0 1px 3px rgba(0,0,0,0.3);
                    ">{host['name']}</div>

                    <!-- Connection Info -->
                    <div style="
                        color: #ffffff;
                        text-align: center;
                        margin-bottom: 12px;
                        font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
                        font-size: 12px;
                        background: rgba(255,255,255,0.25);
                        padding: 8px 12px;
                        border-radius: 8px;
                        border: 1px solid rgba(255,255,255,0.3);
                        font-weight: 500;
                        position: relative;
                        z-index: 1;
                        backdrop-filter: blur(5px);
                    ">{host['username']}@{host['hostname']}:{host['port']}</div>

                    <!-- Auth Icon & Tags -->
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        position: relative;
                        z-index: 1;
                    ">
                        <div style="
                            font-size: 20px;
                            opacity: 0.95;
                            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
                        " title="{'SSH Key' if host.get('auth_method') == 'key' else 'Password'}">{auth_icon}</div>

                        <div style="
                            font-size: 10px;
                            color: {tag_color};
                            background: rgba(255,255,255,0.9);
                            padding: 4px 10px;
                            border-radius: 12px;
                            font-weight: 700;
                            text-transform: uppercase;
                            letter-spacing: 0.5px;
                            border: 1px solid rgba(255,255,255,0.5);
                            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                        ">{tags_str}</div>
                    </div>
                </div>
                """

            html += "</div></div>"

        # Add untagged hosts
        if untagged_hosts:
            html += f"""
            <div style="margin-bottom: 50px;">
                <h3 style="
                    color: #6c757d;
                    margin-bottom: 25px;
                    padding: 18px 30px;
                    background: linear-gradient(135deg, #6c757d15 0%, #6c757d08 100%);
                    border-left: 6px solid #6c757d;
                    border-radius: 0 15px 15px 0;
                    font-size: 22px;
                    font-weight: 700;
                    letter-spacing: 1px;
                    text-transform: uppercase;
                ">
                    📄 UNTAGGED ({len(untagged_hosts)})
                </h3>
                <div style="
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 20px;
                    padding: 0 15px;
                ">
            """

            for host in untagged_hosts:
                auth_icon = "🔑" if host.get('auth_method') == 'key' else "🔐"

                html += f"""
                <div class="host-tile"
                     data-host-name="{host['name']}"
                     style="
                    background: linear-gradient(135deg, #6c757d40 0%, #6c757d60 100%);
                    border: 3px solid #6c757d;
                    border-radius: 12px;
                    padding: 15px 18px;
                    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    cursor: pointer;
                    position: relative;
                    box-shadow: 0 6px 20px rgba(108, 117, 125, 0.3);
                "
                onmouseover="
                    this.style.transform='translateY(-4px) scale(1.01)';
                    this.style.boxShadow='0 12px 30px rgba(108, 117, 125, 0.5)';
                    this.style.borderColor='#495057';
                "
                onmouseout="
                    this.style.transform='translateY(0) scale(1)';
                    this.style.boxShadow='0 6px 20px rgba(108, 117, 125, 0.3)';
                    this.style.borderColor='#6c757d';
                "
                onclick="window.connectToHost && window.connectToHost('{host['name']}')">

                    <!-- Host Name -->
                    <div style="
                        font-size: 18px;
                        font-weight: 700;
                        color: #ffffff;
                        margin-bottom: 10px;
                        text-align: center;
                        border-bottom: 2px solid rgba(255,255,255,0.4);
                        padding-bottom: 8px;
                        letter-spacing: 0.3px;
                        text-shadow: 0 1px 3px rgba(0,0,0,0.3);
                    ">{host['name']}</div>

                    <!-- Connection Info -->
                    <div style="
                        color: #ffffff;
                        text-align: center;
                        margin-bottom: 12px;
                        font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
                        font-size: 12px;
                        background: rgba(255,255,255,0.25);
                        padding: 8px 12px;
                        border-radius: 8px;
                        border: 1px solid rgba(255,255,255,0.3);
                        font-weight: 500;
                        backdrop-filter: blur(5px);
                    ">{host['username']}@{host['hostname']}:{host['port']}</div>

                    <!-- Auth Icon & Tags -->
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    ">
                        <div style="
                            font-size: 20px;
                            opacity: 0.95;
                            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
                        " title="{'SSH Key' if host.get('auth_method') == 'key' else 'Password'}">{auth_icon}</div>

                        <div style="
                            font-size: 10px;
                            color: #6c757d;
                            background: rgba(255,255,255,0.9);
                            padding: 4px 10px;
                            border-radius: 12px;
                            font-weight: 700;
                            text-transform: uppercase;
                            letter-spacing: 0.5px;
                            border: 1px solid rgba(255,255,255,0.5);
                            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                        ">NO TAGS</div>
                    </div>
                </div>
                """

            html += "</div></div>"

        html += "</div>"
        return html

    def connect_to_host_by_name(self, host_name):
        """Connect to host by name"""
        if not host_name:
            return "🎯 **Click any tile** to connect to that host"

        # Find the host
        host = None
        for h in self.filtered_hosts:
            if h['name'] == host_name:
                host = h
                break

        if not host:
            return f"❌ **Host '{host_name}' not found**"

        try:
            # Launch the SSH session in a separate thread
            def launch_session():
                self.ssh_manager.launch_iterm_session(host)

            thread = threading.Thread(target=launch_session, daemon=True)
            thread.start()

            return f"""🚀 **Launching SSH session for {host['name']}**

**Connecting to:** `{host['username']}@{host['hostname']}:{host['port']}`

✅ **Check your iTerm2** for the new session tab!

*Session opened with **{host.get('iterm_profile', 'Default')}** profile*"""
        except Exception as e:
            return f"❌ **Connection Error**\n\n{str(e)}"

    def create_interface(self):
        """Create the Gradio interface"""
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

                        # Event handlers
            def update_display_by_search(search_term=""):
                # Clear tag filter when searching
                return self.create_clickable_tiles_html(search_term), "All Tags"

            def update_display_by_tag(tag_filter="All Tags"):
                # Clear search when filtering by tag
                return self.create_clickable_tiles_html("", tag_filter), ""

            # Wire up events
            search_box.change(
                fn=update_display_by_search,
                inputs=[search_box],
                outputs=[hosts_display, tag_filter_dropdown]
            )

            tag_filter_dropdown.change(
                fn=update_display_by_tag,
                inputs=[tag_filter_dropdown],
                outputs=[hosts_display, search_box]
            )

                        # Handle tile clicks through hidden textbox (no UI feedback needed)
            def handle_host_selection(host_name):
                print(f"Python received host selection: '{host_name}'")
                self.connect_to_host_by_name(host_name)
                return host_name  # Just return the host name for the hidden field

            hidden_host_selector.change(
                fn=handle_host_selection,
                inputs=[hidden_host_selector],
                outputs=[hidden_host_selector]  # Output back to itself to clear
            )

                        # Set up the JavaScript function using Gradio's JS integration
            interface.load(
                fn=None,
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

        return interface


def launch_web_interface(config_file="~/.ssh_manager_config.json", share=False, port=7860, silent=False):
    """Launch the web interface"""
    if not silent:
        print("🌐 Starting SSH Session Manager Web Interface...")
        print(f"📁 Using config: {config_file}")

    web_manager = WebSSHManager(config_file)
    interface = web_manager.create_interface()

    if not silent:
        print(f"🚀 Launching on http://localhost:{port}")
        if share:
            print("🔗 Creating shareable link...")

    interface.launch(
        server_port=port,
        share=share,
        show_error=not silent,  # Suppress errors in silent mode
        inbrowser=not silent,   # Don't open browser in silent mode
        quiet=silent            # Suppress Gradio output in silent mode
    )


if __name__ == "__main__":
    launch_web_interface()