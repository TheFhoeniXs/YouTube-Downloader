import flet as ft
from ui.components import DownloadSection,CurrentSelection,DownloadQueue
from models.downloader import RobustDownloader

import shutil
import importlib.util

class StartupCheck:
    def __init__(self, page: ft.Page, on_complete):
        self.page = page
        self.on_complete = on_complete
        self.status_text = ft.Text(
            "Initializing...",
            size=16,
            text_align=ft.TextAlign.CENTER
        )
        self.progress_bar = ft.ProgressBar(
            width=400,
            color=ft.Colors.BLUE,
            bgcolor=ft.Colors.BLUE_100
        )
        
    def check_ffmpeg(self):
        """Check if ffmpeg is installed"""
        return shutil.which("ffmpeg") is not None
    
    def check_ytdlp_installed(self):
        """Check if yt-dlp is installed"""
        return importlib.util.find_spec("yt_dlp") is not None
    
    async def run_checks(self):
        """Run all startup checks"""
        # Check FFmpeg
        self.status_text.value = "Checking FFmpeg installation..."
        self.page.update()
       
        
        if not self.check_ffmpeg():
            self.status_text.value = "FFmpeg not found. Please install FFmpeg to continue."
            self.status_text.color = ft.Colors.RED
            self.progress_bar.visible = False
            self.page.update()
            return False
        
        self.status_text.value = "FFmpeg found ✓"
        self.status_text.color = ft.Colors.GREEN
        self.page.update()
        
        
        # Check yt-dlp
        self.status_text.value = "Checking yt-dlp installation..."
        self.status_text.color = ft.Colors.BLACK
        self.page.update()
        
        
        if not self.check_ytdlp_installed():
            self.status_text.value = "yt-dlp not found. Please install yt-dlp to continue."
            self.status_text.color = ft.Colors.RED
            self.progress_bar.visible = False
            self.page.update()
            return False
        
        self.status_text.value = "yt-dlp found ✓"
        self.status_text.color = ft.Colors.GREEN
        self.page.update()
        
        
        # All checks passed
        self.status_text.value = "All checks completed!"
        self.progress_bar.visible = False
        self.page.update()
        
        # Wait a moment then call the completion callback
        
        self.on_complete()
        
        return True
    
    def get_view(self):
        """Return the startup check view"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Startup Checks",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=20),
                    self.progress_bar,
                    ft.Container(height=20),
                    self.status_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )


def main(page: ft.Page):
    page.title = "Youtube Downlaoder"
    page.padding = 20
    file_picker  = ft.FilePicker()
    downloder = RobustDownloader(3)
    down_queue = DownloadQueue(downloader=downloder,save_path="downloads",file_picker =file_picker)
    down_section = DownloadSection(down_queue.add_video)
    curr_selection = CurrentSelection()
    down_section.subscribe(curr_selection)
    # Main content layout
    main_content = ft.Column(
        expand=True,
        spacing=20,
        controls=[
            # 1. Download Section (sabit yükseklik)
            down_section,
            
            # 2. Middle Section (expand=True ile kalan alanı doldurur)
            ft.Row(
                expand=True,
                #vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    # Current Selection (7 birim genişlik)
                    curr_selection,
                    
                    # Download Queue (5 birim genişlik)  
                    down_queue,
                ],
                spacing=20
            ),
            
            # 3. History Section (sabit yükseklik, sayfanın altına yapışık)
            
            
        ]
    )

    def load_main_content():
        page.clean()
        page.overlay.append(file_picker)
        page.add(main_content)
        page.update()
    

    startup = StartupCheck(page, load_main_content)
    page.add(startup.get_view())
    page.run_task(startup.run_checks)


if __name__ == "__main__":
    ft.app(main)