import wx
import os
import requests
import threading
from pytube import YouTube, Playlist
# import string
import sys


class YoutubeDownloader(wx.Frame):
    def __init__(self, parent, title):
        super(YoutubeDownloader, self).__init__(parent, title=title, size=(500, 300))

        # Determine if the script is bundled into an executable
        if getattr(sys, 'frozen', False):
            # Running as a bundled executable
            script_dir = sys._MEIPASS   # type: ignore
        else:
            # Running as a script
            script_dir = os.path.abspath(os.path.dirname(__file__))

        # Construct the path to the icon file
        icon_path = os.path.join(script_dir, "utube", "icon.ico")

        # Set the icon using the constructed path
        self.SetIcon(wx.Icon(icon_path, wx.BITMAP_TYPE_ICO))

        # Center the window on the screen
        self.Center()

        # Set a fixed window size
        self.SetMinSize((700, 800))
        self.SetMaxSize((700, 800))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        # Add a Listbox for displaying downloaded files
        self.downloaded_files_listbox = wx.ListBox(panel, size=(400, 150),
                                                   style=wx.LB_EXTENDED | wx.LB_HSCROLL | wx.LB_NEEDED_SB)
        vbox.Add(self.downloaded_files_listbox, flag=wx.ALL, border=10)

        # Widgets
        url_label = wx.StaticText(panel, label="Enter YouTube URL:")
        self.url_entry = wx.TextCtrl(panel, size=(400, -1))
        video_resolution_label = wx.StaticText(panel, label="Select Video Resolution:")
        video_resolution_choices = ["Highest", "720p", "480p"]
        self.video_resolution_dropdown = wx.ComboBox(panel, choices=video_resolution_choices, style=wx.CB_READONLY)
        self.video_resolution_dropdown.SetValue("Highest")
        audio_quality_label = wx.StaticText(panel, label="Select Audio Quality:")
        audio_quality_choices = ["Highest", "256kbps", "128kbps"]
        self.audio_quality_dropdown = wx.ComboBox(panel, choices=audio_quality_choices, style=wx.CB_READONLY)
        self.audio_quality_dropdown.SetValue("Highest")
        save_path_label = wx.StaticText(panel, label="Save Path:")
        self.save_path_entry = wx.TextCtrl(panel, size=(400, -1))
        select_path_button = wx.Button(panel, label="Select Path")
        select_path_button.Bind(wx.EVT_BUTTON, self.select_save_path)
        download_button = wx.Button(panel, label="Download")
        download_button.Bind(wx.EVT_BUTTON, self.download_youtube_video)
        self.progress_bar = wx.Gauge(panel, range=100)
        self.percentage_label = wx.StaticText(panel, label="")
        self.result_label = wx.StaticText(panel, label="")
        self.save_label = wx.StaticText(panel, label="")

        # Checkbox for audio download
        self.audio_checkbox = wx.CheckBox(panel, label="Download Audio")
        self.audio_checkbox.SetValue(True)  # Default: Download audio

        # Layout
        vbox.Add(url_label, flag=wx.ALL, border=10)
        vbox.Add(self.url_entry, flag=wx.ALL, border=10)
        vbox.Add(video_resolution_label, flag=wx.ALL, border=10)
        vbox.Add(self.video_resolution_dropdown, flag=wx.ALL, border=10)
        vbox.Add(audio_quality_label, flag=wx.ALL, border=10)
        vbox.Add(self.audio_quality_dropdown, flag=wx.ALL, border=10)
        vbox.Add(save_path_label, flag=wx.ALL, border=10)
        vbox.Add(self.save_path_entry, flag=wx.ALL, border=10)
        vbox.Add(select_path_button, flag=wx.ALL, border=10)
        vbox.Add(self.audio_checkbox, flag=wx.ALL, border=10)
        vbox.Add(download_button, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(self.progress_bar, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.percentage_label, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)
        vbox.Add(self.result_label, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)
        vbox.Add(self.save_label, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)
        # Add a Listbox for displaying downloaded files
        self.downloaded_files_listbox = wx.ListBox(panel, size=(400, 150),
                                                   style=wx.LB_EXTENDED | wx.LB_HSCROLL | wx.LB_NEEDED_SB)
        vbox.Add(self.downloaded_files_listbox, flag=wx.ALL, border=10)

        status_bar = self.CreateStatusBar(2)
        status_bar.SetStatusText("by Sajid Hussain", 1)  # "1" indicates the rightmost field

        panel.SetSizer(vbox)

    def select_save_path(self, _):
        with wx.DirDialog(self, "Choose a directory", style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.save_path_entry.SetValue(dlg.GetPath())

    def download_youtube_playlist(self, playlist_url, output_path, video_resolution, audio_quality, download_audio):
        try:
            playlist = Playlist(playlist_url)
            for video_url in playlist.video_urls:
                self.download_thread(video_url, output_path, video_resolution, audio_quality, download_audio)

            wx.CallAfter(self.result_label.SetLabel, "Playlist download successful!")

        except Exception as e:
            wx.CallAfter(self.result_label.SetLabel, f"Error: {e}")
            print(f"Error: {e}")

    def download_youtube_video(self, _):
        video_url = self.url_entry.GetValue()
        output_path = self.save_path_entry.GetValue()
        video_resolution = self.video_resolution_dropdown.GetValue()
        audio_quality = self.audio_quality_dropdown.GetValue()
        download_audio = self.audio_checkbox.GetValue()

        # Check if the provided URL is a playlist
        if "playlist" in video_url.lower():
            threading.Thread(target=self.download_youtube_playlist,
                             args=(video_url, output_path, video_resolution, audio_quality, download_audio)).start()
        else:
            threading.Thread(target=self.download_thread,
                             args=(video_url, output_path, video_resolution, audio_quality, download_audio)).start()

    def download_thread(self, video_url, output_path, video_resolution, audio_quality, download_audio):
        try:
            youtube = YouTube(video_url)

            # Get video stream
            video_stream = self.get_stream_by_resolution(youtube, video_resolution, "mp4")
            audio_response = None
            # Get audio stream if selected
            audio_stream = None
            if download_audio:
                audio_stream = self.get_stream_by_resolution(youtube, audio_quality, "mp4", audio=True)

            if not video_stream or (download_audio and not audio_stream):
                raise Exception("No suitable streams found with selected video or audio quality.")

            # Set up progress bar
            total_size = int(video_stream.filesize)
            if download_audio:
                total_size += int(audio_stream.filesize)
            wx.CallAfter(self.progress_bar.SetRange, total_size)
            wx.CallAfter(self.progress_bar.SetValue, 0)

            # Check if the file already exists, add an index if needed
            file_index = 1
            sanitized_title = ''.join(char for char in youtube.title if char.isalnum() or char in (' ', '_', '-'))
            while os.path.exists(f"{output_path}\\{sanitized_title}_{file_index}.mp4"):
                file_index += 1

            # Download video and audio in chunks
            video_response = requests.get(video_stream.url, stream=True)

            # If audio download is selected, also download audio in chunks
            if download_audio:
                audio_response = requests.get(audio_stream.url, stream=True)

            # Replace forward slashes with backslashes in the file path
            output_path = output_path.replace('/', '\\')

            # Open the file in binary write mode
            with open(f"{output_path}\\{sanitized_title}_{file_index}.mp4", 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=1024):
                    f.write(chunk)
                    wx.CallAfter(self.update_progress, len(chunk))

                if download_audio:
                    for chunk in audio_response.iter_content(chunk_size=1024):
                        f.write(chunk)
                        wx.CallAfter(self.update_progress, len(chunk))

            wx.CallAfter(self.result_label.SetLabel, "Download successful!")

            # Save the location and update the listbox
            file_path = f"{output_path}\\{sanitized_title}_{file_index}.mp4"
            self.save_location(file_path)

        except Exception as e:
            wx.CallAfter(self.result_label.SetLabel, f"Error: {e}")
            print(f"Error: {e}")

    @staticmethod
    def get_stream_by_resolution(youtube, resolution, file_extension, audio=False):
        try:
            if resolution == "Highest":
                if audio:
                    return youtube.streams.filter(only_audio=True, file_extension=file_extension).first()
                else:
                    return youtube.streams.filter(progressive=True,
                                                  file_extension=file_extension).get_highest_resolution()
            else:
                if audio:
                    return youtube.streams.filter(only_audio=True, file_extension=file_extension).first()
                else:
                    return youtube.streams.filter(progressive=True, resolution=resolution,
                                                  file_extension=file_extension).first()
        except Exception as e:
            raise Exception(f"Error getting stream: {e}")

    def update_progress(self, chunk_size):
        current_value = self.progress_bar.GetValue()
        self.progress_bar.SetValue(current_value + chunk_size)
        total_size = self.progress_bar.GetRange()
        percentage = (current_value + chunk_size) / total_size * 100
        wx.CallAfter(self.percentage_label.SetLabel, f"{percentage:.2f}%")

    def save_location(self, file_path):
        try:
            if file_path:
                pass
                # self.save_label.SetLabel(f"Video saved at: {file_path}")
        except Exception as e:
            wx.CallAfter(self.result_label.SetLabel, f"Error: {e}")

    def save_location(self, file_path):
        try:
            if file_path:
                # Update the Listbox with the new file path
                wx.CallAfter(self.update_download_list, file_path)
        except Exception as e:
            wx.CallAfter(self.result_label.SetLabel, f"Error: {e}")

    def update_download_list(self, file_path):
        self.downloaded_files_listbox.Append(file_path)


if __name__ == "__main__":
    app = wx.App(False)
    frame = YoutubeDownloader(None, "YouTube Video Downloader")
    frame.Show()
    app.MainLoop()
