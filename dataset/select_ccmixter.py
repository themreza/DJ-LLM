"""
A script to help with selecting music from ccMixter for the dataset.
It provides a TUI interface, displaying metadata for each file, with the possibility
of listening to each track.
Before using this script, first run fetch_ccmixter.py to fetch data from ccMixter.
"""

import json
import os
from pathlib import Path
import ssl
import time
from typing import Set
import urllib.request
import urllib.error
import tempfile
from mutagen.mp3 import MP3

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Button
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.reactive import reactive


try:
    import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


class MusicPlayer:
    def __init__(self):
        self.current_file = None
        self.playing = False
        self.temp_dir = tempfile.mkdtemp()
        self.duration = 0.0
        self.start_time = 0.0
        if AUDIO_AVAILABLE:
            pygame.mixer.init()

    def play(self, url: str):
        if not AUDIO_AVAILABLE:
            return (False, "pygame not available")

        try:
            self.stop()

            local_path = os.path.join(self.temp_dir, "current.mp3")

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(url)
            req.add_header('Referer', 'https://ccmixter.org/')
            req.add_header('User-Agent', 'DJ-LLM')

            with urllib.request.urlopen(req, context=ssl_context) as response:
                with open(local_path, 'wb') as out_file:
                    out_file.write(response.read())

            if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
                return (False, "Download failed or empty file")

            try:
                audio = MP3(local_path)
                self.duration = audio.info.length
            except Exception:
                self.duration = 0.0

            pygame.mixer.music.load(local_path)
            pygame.mixer.music.play()
            self.playing = True
            self.current_file = local_path
            self.start_time = time.time()
            return (True, "Playing")
        except urllib.error.URLError as e:
            return (False, f"Network error: {e.reason}")
        except Exception as e:
            return (False, f"Error: {str(e)}")

    def stop(self):
        if not AUDIO_AVAILABLE:
            return

        if self.playing:
            pygame.mixer.music.stop()
            self.playing = False

        if self.current_file and os.path.exists(self.current_file):
            try:
                os.remove(self.current_file)
            except:
                pass
            self.current_file = None

    def is_playing(self) -> bool:
        if not AUDIO_AVAILABLE:
            return False
        return self.playing and pygame.mixer.music.get_busy()

    def seek_forward(self, seconds: int = 5) -> None:
        if not AUDIO_AVAILABLE or not self.playing or not self.current_file:
            return
        try:
            current_pos, _ = self.get_position()
            new_pos = min(current_pos + seconds, self.duration)

            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.current_file)
            pygame.mixer.music.play(start=new_pos)
            self.start_time = time.time() - new_pos
        except Exception:
            pass

    def seek_backward(self, seconds: int = 5) -> None:
        if not AUDIO_AVAILABLE or not self.playing or not self.current_file:
            return
        try:
            current_pos, _ = self.get_position()
            new_pos = max(0, current_pos - seconds)

            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.current_file)
            pygame.mixer.music.play(start=new_pos)
            self.start_time = time.time() - new_pos
        except Exception:
            pass

    def get_position(self) -> tuple[float, float]:
        if not AUDIO_AVAILABLE or not self.playing:
            return (0.0, 0.0)
        try:
            elapsed = time.time() - self.start_time
            return (elapsed, self.duration)
        except Exception:
            return (0.0, 0.0)

    def cleanup(self):
        self.stop()
        try:
            os.rmdir(self.temp_dir)
        except:
            pass


class MetadataPanel(Static):
    upload_data = reactive(None)
    selected_file_index = reactive(0)

    def watch_upload_data(self, data):
        self.selected_file_index = 0
        self.refresh_display()

    def watch_selected_file_index(self, index):
        self.refresh_display()

    def refresh_display(self):
        if self.upload_data:
            self.update(self.render_metadata(self.upload_data, self.selected_file_index))
        else:
            self.update("Select an upload to view metadata")

    def render_metadata(self, data, selected_file_index=0) -> str:
        extra = data.get("upload_extra", {})
        files = data.get("files", [])

        files_list = ""
        for i, f in enumerate(files):
            marker = "▶" if i == selected_file_index else " "
            file_size = f.get('file_filesize', '')
            file_name = f.get('file_name', 'Unknown')
            files_list += f"{marker} [{i}] {file_name} {file_size}\n"

        content = f"""[bold cyan]{data['upload_name']}[/bold cyan]

[yellow]Artist:[/yellow] {data.get('user_real_name', 'N/A')}
[yellow]Upload ID:[/yellow] {data['upload_id']}
[yellow]Date:[/yellow] {data.get('upload_date_format', 'N/A')}
[yellow]License:[/yellow] {data.get('license_name', 'N/A')}
[yellow]Tags:[/yellow] {extra.get('usertags', 'N/A')}
[yellow]BPM:[/yellow] {extra.get('bpm', 'N/A')}
[yellow]Scores:[/yellow] {data.get('upload_num_scores', 0)}

[yellow]Versions:[/yellow]
{files_list}
[yellow]Description:[/yellow]
{data.get('upload_description_plain', 'N/A')[:300]}

[yellow]Page:[/yellow] {data.get('file_page_url', 'N/A')}
"""
        return content


class StatusPanel(Static):
    status_text = reactive("Ready")
    progress_text = reactive("")

    def watch_status_text(self, text):
        self.refresh_display()

    def watch_progress_text(self, text):
        self.refresh_display()

    def refresh_display(self):
        if self.progress_text:
            self.update(f"[bold]{self.status_text}[/bold] {self.progress_text}")
        else:
            self.update(f"[bold]{self.status_text}[/bold]")


class CCMixterBrowser(App):
    TITLE = "DJ LLM - ccMixter dataset browser"
    CSS = """
    Screen {
        layout: vertical;
    }

    #main_container {
        layout: horizontal;
        height: 1fr;
    }

    #uploads_container {
        width: 50%;
        border: solid green;
        padding: 1;
    }

    #right_panel {
        width: 50%;
        layout: vertical;
    }

    #metadata_container {
        height: 1fr;
        border: solid blue;
        padding: 1;
        overflow-y: auto;
    }

    #controls_container {
        height: auto;
        min-height: 8;
        border: solid yellow;
        padding: 1;
    }

    DataTable {
        height: 100%;
    }

    DataTable > .datatable--header {
        text-style: bold;
    }

    MetadataPanel {
        height: 100%;
        overflow-y: auto;
    }

    StatusPanel {
        height: 1;
        background: $boost;
        color: $text;
        padding: 0 1;
        margin-bottom: 1;
    }

    Button {
        margin: 0 1;
    }

    Horizontal {
        height: auto;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("space", "toggle_select", "Select/Unselect"),
        Binding("p", "play_music", "Play/Stop"),
        Binding("shift+up", "prev_file", "Shift+↑ Version", show=True),
        Binding("shift+down", "next_file", "Shift+↓ Version", show=True),
        Binding("left", "seek_backward", "Seek -5s", show=True, priority=True),
        Binding("right", "seek_forward", "Seek +5s", show=True, priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.uploads = []
        self.selected_ids: Set[int] = set()
        self.player = MusicPlayer()
        self.current_upload = None
        self.current_upload_id = None
        self.current_track_name = ""
        self.data_file = Path("dataset/ccmixter_data.jsonl")
        self.selection_file = Path("dataset/selected_uploads.txt")

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main_container"):
            with Container(id="uploads_container"):
                yield DataTable(id="uploads_table", cursor_type="row")

            with Vertical(id="right_panel"):
                with Container(id="metadata_container"):
                    yield Static("Metadata", classes="label")
                    yield MetadataPanel(id="metadata_panel")

                with Vertical(id="controls_container"):
                    yield Static("Controls", classes="label")
                    yield StatusPanel(id="status_panel")
                    with Horizontal():
                        yield Button("Play Mode: Off", id="btn_play_stop", variant="error")
                        yield Button("Toggle Select", id="btn_select", variant="primary")

        yield Footer()

    def on_mount(self) -> None:
        self.load_data()
        self.load_selections()
        self.setup_table()
        self.populate_table()
        self.set_interval(0.5, self.update_progress)

    def load_data(self):
        with open(self.data_file, 'r') as f:
            self.uploads = [json.loads(line) for line in f]

    def load_selections(self):
        if self.selection_file.exists():
            with open(self.selection_file, 'r') as f:
                self.selected_ids = {int(line.strip()) for line in f if line.strip()}

    def save_selections(self):
        with open(self.selection_file, 'w') as f:
            for upload_id in sorted(self.selected_ids):
                f.write(f"{upload_id}\n")

    def setup_table(self):
        table = self.query_one("#uploads_table", DataTable)
        table.add_column("Selected", width=8)
        table.add_column("ID", width=8)
        table.add_column("Name", width=30)
        table.add_column("Artist", width=15)
        table.add_column("BPM", width=8)
        table.add_column("Tags", width=20)
        table.add_column("Files", width=5)
        table.cursor_type = "row"

    def populate_table(self):
        table = self.query_one("#uploads_table", DataTable)
        for upload in self.uploads:
            upload_id = upload["upload_id"]
            selected = "✓" if upload_id in self.selected_ids else " "
            extra = upload.get("upload_extra", {})
            tags = extra.get("usertags", "")

            upload_name = str(upload["upload_name"])
            artist_name = str(upload.get("user_real_name", ""))
            bpm = str(extra.get("bpm", ""))
            if not bpm:
                bpm = "-"

            table.add_row(
                selected,
                str(upload_id),
                upload_name,
                artist_name,
                bpm,
                tags,
                str(len(upload.get("files", []))),
                key=str(upload_id)
            )

    def on_data_table_row_highlighted(self, event):
        upload_id = int(event.row_key.value)

        if upload_id == self.current_upload_id:
            return

        self.current_upload_id = upload_id
        self.current_upload = next((u for u in self.uploads if u["upload_id"] == upload_id), None)

        if self.current_upload:
            metadata_panel = self.query_one("#metadata_panel", MetadataPanel)
            metadata_panel.upload_data = self.current_upload
            metadata_panel.selected_file_index = 0

            if self.player.is_playing():
                self.play_current_file()

    def action_toggle_select(self):
        if not self.current_upload:
            self.update_status("No upload selected")
            return

        upload_id = self.current_upload["upload_id"]
        table = self.query_one("#uploads_table", DataTable)

        if upload_id in self.selected_ids:
            self.selected_ids.remove(upload_id)
            status = "Unselected"
        else:
            self.selected_ids.add(upload_id)
            status = "Selected"

        self.save_selections()
        self.refresh_table_row(upload_id)
        self.update_status(f"{status} upload {upload_id}")

    def refresh_table_row(self, upload_id: int):
        table = self.query_one("#uploads_table", DataTable)

        selected = "✓" if upload_id in self.selected_ids else " "

        row_key = str(upload_id)

        try:
            from textual.coordinate import Coordinate
            row_index = table.get_row_index(row_key)
            coord = Coordinate(row_index, 0)
            table.update_cell_at(coord, selected)
        except Exception:
            pass

    def play_current_file(self):
        if not self.current_upload:
            self.update_status("No upload selected")
            return

        files = self.current_upload.get("files", [])
        if not files:
            self.update_status("No files available")
            return

        metadata_panel = self.query_one("#metadata_panel", MetadataPanel)
        file_index = metadata_panel.selected_file_index

        if file_index >= len(files):
            file_index = 0

        mp3_file = files[file_index]
        url = mp3_file.get("download_url")

        if url:
            self.current_track_name = mp3_file['file_name']
            self.update_status(f"Loading: {self.current_track_name}")
            success, message = self.player.play(url)
            if success:
                self.update_status(f"Playing: {self.current_track_name}")
            else:
                self.update_status(f"Failed: {message}")
                self.current_track_name = ""
        else:
            self.update_status("No download URL available")

    def action_play_music(self):
        if self.player.is_playing():
            self.action_stop_music()
            self.update_play_button()
            return

        self.play_current_file()
        self.update_play_button()

    def action_stop_music(self):
        self.player.stop()
        self.current_track_name = ""
        self.update_status("Stopped")

    def action_next_file(self):
        if not self.current_upload:
            return

        files = self.current_upload.get("files", [])
        if not files:
            return

        metadata_panel = self.query_one("#metadata_panel", MetadataPanel)
        metadata_panel.selected_file_index = (metadata_panel.selected_file_index + 1) % len(files)

    def action_prev_file(self):
        if not self.current_upload:
            return

        files = self.current_upload.get("files", [])
        if not files:
            return

        metadata_panel = self.query_one("#metadata_panel", MetadataPanel)
        metadata_panel.selected_file_index = (metadata_panel.selected_file_index - 1) % len(files)

    def action_seek_forward(self):
        if self.player.is_playing():
            self.player.seek_forward(5)

    def action_seek_backward(self):
        if self.player.is_playing():
            self.player.seek_backward(5)

    def on_button_pressed(self, event):
        if event.button.id == "btn_play_stop":
            self.action_play_music()
            self.update_play_button()
        elif event.button.id == "btn_select":
            self.action_toggle_select()

    def update_status(self, text: str):
        status_panel = self.query_one("#status_panel", StatusPanel)
        status_panel.status_text = text

    def update_play_button(self) -> None:
        button = self.query_one("#btn_play_stop", Button)
        if self.player.is_playing():
            button.label = "Play Mode: On"
            button.variant = "success"
        else:
            button.label = "Play Mode: Off"
            button.variant = "error"

    def update_progress(self) -> None:
        was_playing = self.player.is_playing()

        if was_playing:
            pos, duration = self.player.get_position()
            if pos > 0 and duration > 0:
                pos_mins = int(pos // 60)
                pos_secs = int(pos % 60)
                dur_mins = int(duration // 60)
                dur_secs = int(duration % 60)
                status_panel = self.query_one("#status_panel", StatusPanel)
                status_panel.progress_text = f"[{pos_mins:02d}:{pos_secs:02d}/{dur_mins:02d}:{dur_secs:02d}]"
        else:
            status_panel = self.query_one("#status_panel", StatusPanel)
            status_panel.progress_text = ""

        self.update_play_button()

    def on_unmount(self):
        self.player.cleanup()


if __name__ == "__main__":
    app = CCMixterBrowser()
    app.run()
