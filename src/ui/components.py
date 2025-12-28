from datetime import datetime
import flet as ft
from .style import AppColors
from models.validators import is_youtube_link_checker, get_video_info
from models.video_info import VideoInfo
from abc import ABC, abstractmethod
from models.downloader import RobustDownloader
from typing import Callable


class VideoQuearySelection(ABC):
    @abstractmethod
    def on_video_info(self,info: VideoInfo, **kwargs):
        pass


class DownloadSection(ft.Container):
    def __init__(self,add_task:Callable):
        super().__init__(bgcolor=AppColors.SURFACE_DARK,border_radius=16,border=ft.border.all(1, "white10"),padding=32)
        self._observers: list[VideoQuearySelection] = []
        self.current_video_info: VideoInfo
        self.download_btn_is_active = False
        self.add_task = add_task

        self.url_input = ft.TextField(
                hint_text="https://www.youtube.com/watch?v=...",
                hint_style=ft.TextStyle(color="white20", size=16),
                text_style=ft.TextStyle(color="white", size=16, weight=ft.FontWeight.W_500),
                border_color="transparent",
                focused_border_color="transparent",
                bgcolor="transparent",
                expand=True,
                content_padding=0,
                on_blur= self._url_input_blur
            )
        
        self.format_dropdown = ft.Dropdown(
            width=140,
            bgcolor=AppColors.SURFACE_ACCENT,
            border_color="white10",
            focused_border_color=AppColors.PRIMARY,
            text_style=ft.TextStyle(color="white", size=13, weight=ft.FontWeight.BOLD),
            options=[
            ],
            border_radius=12
        )

        self.download_btn = ft.Container(
            height=64,
            bgcolor=AppColors.PRIMARY,
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=32),
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DOWNLOAD, color="black", size=20),
                    ft.Text("Download", size=15, weight=ft.FontWeight.BOLD, color="black")
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=f"{AppColors.PRIMARY}4D",
            ),
            on_click=self._on_button_click
        )

        self.content = ft.Column(
                controls=[
                    ft.Text(
                        spans=[
                            ft.TextSpan("Paste link to start ", style=ft.TextStyle(color="white", size=32, weight=ft.FontWeight.BOLD)),
                            ft.TextSpan("downloading", style=ft.TextStyle(color=AppColors.PRIMARY, size=32, weight=ft.FontWeight.BOLD))
                        ]
                    ),
                    ft.Container(height=24),
                    ft.Row(
                        controls=[
                            ft.Container(
                                bgcolor=AppColors.SURFACE_ACCENT,
                                border_radius=12,
                                border=ft.border.all(1, "white10"),
                                padding=ft.padding.only(left=20, right=8, top=8, bottom=8),
                                expand=True,
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.LINK, color=AppColors.PRIMARY, size=20),
                                        self.url_input,
                                        ft.TextButton(
                                            "PASTE",
                                            style=ft.ButtonStyle(
                                                color="white60",
                                                bgcolor="white10",
                                                padding=ft.padding.symmetric(horizontal=16, vertical=8)
                                            )
                                        )
                                    ],
                                    spacing=12
                                )
                            ),
                            self.format_dropdown,
                            self.download_btn
                        ],
                        spacing=12
                    )
                ],
                spacing=0
            )
        
    
    def _url_input_blur(self,e):
        if not e.control.value: return

        if self.page:
            self.page.run_task(self._validate_and_fetch_video_info,e)

    async def _validate_and_fetch_video_info(self,e):
        url = e.control.value.strip()

        if not is_youtube_link_checker(url=url):
            e.control.error_text = "❌ Invalid YouTube URL"
            e.control.border_color = ft.Colors.RED
            self.download_btn.bgcolor = AppColors.PASSİVE
            self.download_btn_is_active = False
            self.update()
            return
        self.format_dropdown.options = []
        e.control.error_text = None
        e.control.border_color = ft.Colors.BLUE

        self._loading_state()

        try:
            print(f"🔍 Fetching video info for: {url}")
            video_info = await get_video_info(url=url)
            self._succes_state(video_info=video_info)
        except Exception as e:
            print(f"❌ Error: {e}")
            self._error_state(str(e))
    
    def _loading_state(self):
        self.download_btn.bgcolor = AppColors.SURFACE_ACCENT
        self.download_btn.content = ft.Row(
            controls=[
                ft.ProgressRing(width=16, height=16, stroke_width=2, color="white"),
                ft.Text("Checking...", size=15, weight=ft.FontWeight.BOLD, color="white")
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER
        )
        self.download_btn_is_active = False
        self.update()

    def _succes_state(self,video_info):
        print(f"✅ Video found: {video_info.title}")
        
        self.current_video_info = video_info
        self.download_btn.bgcolor = AppColors.PRIMARY
        self.download_btn.shadow.color = AppColors.PRIMARY  # type: ignore
        self.download_btn.content = ft.Row(
            controls=[
                ft.Icon(ft.Icons.DOWNLOAD, color="black", size=20),
                ft.Text("Download", size=15, weight=ft.FontWeight.BOLD, color="black")
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER
        )
        self._update_format_dropdown()
        self._notify(video_info)
        self.download_btn_is_active = True
        self.update()
    
    def _error_state(self, error_message: str):
        """Hata durumu"""
        self.url_input.error_text = f"❌ {error_message}"
        self.url_input.border_color = ft.Colors.RED
        self.download_btn.bgcolor = AppColors.PASSİVE
        self.download_btn.content = ft.Row(
            controls=[
                ft.Icon(ft.Icons.ERROR_OUTLINE, color="black", size=20),
                ft.Text("Failed", size=15, weight=ft.FontWeight.BOLD, color="black")
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER
        )
        self.download_btn_is_active = False
        self.update()
    
    def _update_format_dropdown(self):
        self.format_dropdown.options = [ft.dropdown.Option(x) for x in self.current_video_info.available_qualities]
        self.format_dropdown.value= self.current_video_info.available_qualities[0]
        self.update()

    def subscribe(self, obs: VideoQuearySelection): self._observers.append(obs)
    
    def _notify(self,info:VideoInfo):
        for obs in self._observers:
            obs.on_video_info(info)
    
    def _on_button_click(self,e):
        if self.page:
            self.page.run_task(self.add_task,self.current_video_info,self.format_dropdown.value[:-1]) # type: ignore
 

class CurrentSelection(ft.Container,VideoQuearySelection):
    def __init__(self):
        super().__init__(expand=6)

        self.channel_name= ft.Text(value="by TheFhoeniXs",size=11,weight=ft.FontWeight.W_500,color="white40")
        self.video_title= ft.Text(value="TheFhoneniXs",size=18,weight=ft.FontWeight.BOLD,color="white")
        self.video_times= ft.Text(value="12:45", size=9, weight=ft.FontWeight.BOLD, color="black")

        self.video_thumbnail_url = ft.Image(src=f"assets/icon.png",fit=ft.ImageFit.COVER,border_radius=12,opacity=0.8)
        self.max_quality = ft.Text("4K HDR", size=9, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)

        self.content = ft.Column(
            controls=[
                ft.Text("CURRENT SELECTION", size=10, weight=ft.FontWeight.BOLD, color="white40"),
                ft.Container(height=16),
                ft.Container(
                    bgcolor=AppColors.SURFACE_DARK,
                    border_radius=16,
                    border=ft.border.all(1, "white10"),
                    padding=16,
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                width=320,
                                height=180,
                                border_radius=12,
                                bgcolor="#000000",
                                border=ft.border.all(1, "white10"),
                                content=ft.Stack(
                                    controls=[
                                        self.video_thumbnail_url,
                                        ft.Container(
                                            bgcolor="#FF6A00",
                                            border_radius=4,
                                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                            bottom=8,
                                            right=8,
                                            content=self.video_times
                                        )
                                    ]
                                )
                            ),
                            ft.Container(width=24),
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Container(
                                                bgcolor="#DC262633",
                                                border=ft.border.all(1, "#DC26264D"),
                                                border_radius=4,
                                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                                content=ft.Text("YOUTUBE", size=9, weight=ft.FontWeight.BOLD, color="#DC2626")
                                            ),
                                            ft.Container(
                                                bgcolor=f"{AppColors.PRIMARY}1A",
                                                border=ft.border.all(1, f"{AppColors.PRIMARY}33"),
                                                border_radius=4,
                                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                                content=self.max_quality
                                            )
                                        ],
                                        spacing=8
                                    ),
                                    ft.Container(height=12),
                                    self.video_title,
                                    self.channel_name,
                                    ft.Container(height=16),
                                    ft.Row(
                                        controls=[
                                            ft.Container(
                                                bgcolor=AppColors.SURFACE_ACCENT,
                                                border=ft.border.all(1, "white10"),
                                                border_radius=8,
                                                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                                content=ft.Row(
                                                    controls=[
                                                        ft.Icon(ft.Icons.HD, size=14, color="white"),
                                                        ft.Text("Video", size=11, weight=ft.FontWeight.W_500, color="white")
                                                    ],
                                                    spacing=6
                                                )
                                            ),
                                            ft.Container(
                                                bgcolor=AppColors.SURFACE_ACCENT,
                                                border=ft.border.all(1, "white10"),
                                                border_radius=8,
                                                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                                content=ft.Row(
                                                    controls=[
                                                        ft.Icon(ft.Icons.MUSIC_NOTE, size=14, color="white"),
                                                        ft.Text("Audio", size=11, weight=ft.FontWeight.W_500, color="white")
                                                    ],
                                                    spacing=6
                                                )
                                            ),
                                            ft.Container(
                                                bgcolor=AppColors.SURFACE_ACCENT,
                                                border=ft.border.all(1, "white10"),
                                                border_radius=8,
                                                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                                content=ft.Row(
                                                    controls=[
                                                        ft.Icon(ft.Icons.CLOSED_CAPTION, size=14, color="white"),
                                                        ft.Text("Subs", size=11, weight=ft.FontWeight.W_500, color="white")
                                                    ],
                                                    spacing=6
                                                )
                                            )
                                        ],
                                        spacing=8,
                                        wrap=True
                                    )
                                ],
                                spacing=0,
                                expand=True
                            )
                        ],
                        spacing=0
                    )
                )
            ],
            spacing=0
        )

    def on_video_info(self, info: VideoInfo, **kwargs):
        self.channel_name.value = info.channel
        self.video_title.value = info.short_title
        self.video_times.value = info.duration_formatted
        self.video_thumbnail_url.src = info.thumbnail_url
        self.max_quality.value = info.available_qualities[0]
        self.update()


class DownloadQueue(ft.Container):
    def __init__(self,downloader: RobustDownloader,file_picker:ft.FilePicker,save_path:str = "downloads"):
       super().__init__(expand=5)
       self.downloader = downloader
       self.save_path = save_path
       self.file_picker =file_picker
       self.queue_column = ft.Column(
           expand=True,
           spacing=10,
           scroll=ft.ScrollMode.ALWAYS,
           controls=[]
       )
       self.tasks = {}
       self.task_counter = 0
       self.content = ft.Column(
            expand=True,
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("DOWNLOAD QUEUE", size=10, weight=ft.FontWeight.BOLD, color="white40"),
                        ft.Container(expand=True),
                        ft.TextButton("CLEAR ALL", style=ft.ButtonStyle(color=AppColors.PRIMARY, padding=0))
                    ]
                ),
                ft.Container(height=16),
                ft.Container(
                    expand=True,
                    content=self.queue_column
                )
            ]
        )

    async def add_video(self,info:VideoInfo,res:str):
        self.task_counter += 1
        video_ids = f"video_{self.task_counter}_{int(datetime.now().timestamp())}"

        task = VideoTask(video_id=video_ids,downloader=self.downloader,video_info=info,save_path=self.save_path,resolution=res,queue_ref=self,file_picker=self.file_picker) 

        self.tasks[video_ids] = task
        self.queue_column.controls.insert(0,task)
        self.update()

    async def remove_task(self, video_id):
        if video_id in self.tasks:
            task = self.tasks[video_id]
            self.queue_column.controls.remove(task)
            del self.tasks[video_id]
            self.update()

        
class VideoTask(ft.Container):
    def __init__(self, video_id, downloader:RobustDownloader, video_info:VideoInfo, save_path:str, resolution:str, queue_ref:DownloadQueue,file_picker:ft.FilePicker):
        super().__init__(
            bgcolor="#1A1D24",  # AppColors.AppColors.SURFACE_DARK
            border_radius=12,
            border=ft.border.all(1, "white10"),
            padding=12,
            animate=ft.Animation(320, ft.AnimationCurve.EASE_OUT),
            on_hover= self._on_hover,
            height= 75,
        )

        self.downloader = downloader
        self.video_info = video_info
        self.video_id = video_id   
        self.save_path = save_path
        self.resolutions = resolution
        self.queue_ref = queue_ref
        self.file_picker =file_picker
        self.file_picker.on_result = self._file_picker
        self.status = "waiting"  # waiting, downloading, completed, cancelled, error
        # UI Components
        self.video_title = ft.Text(
            value=f"({self.resolutions}p) "+self.video_info.short_title, 
            size=11, 
            weight=ft.FontWeight.BOLD, 
            color="white", 
            expand=True
        )
        self.pb_percent = ft.Text(
            "0%", 
            size=11, 
            weight=ft.FontWeight.BOLD, 
            color="#FF6A00"
        )
        self.pb = ft.ProgressBar(
            value=0, 
            height=4, 
            border_radius=2, 
            color="#FF6A00"
        )
        self.download_speed = ft.Text(
            "0.0 MB/s", 
            size=9, 
            weight=ft.FontWeight.W_500, 
            color="white40"
        )
        self.left_time = ft.Text(
            "-- mins left", 
            size=9, 
            weight=ft.FontWeight.W_500, 
            color="#FF6A00CC"
        )
        self.button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            icon_color="white70",
            icon_size=18,
            bgcolor="#242830",
            width=32,
            height=32,
            on_click=self.start_download
        )
        self.button_cancel = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color="white70",
            icon_size=18,
            bgcolor="#242830",
            width=32,
            height=32,
            visible=False,
            on_click=self.cancel_download
        )
        self.button_rm = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color="white70",
            icon_size=18,
            bgcolor="#242830",
            width=32,
            height=32,
            on_click=self.remove_from_queue
        )
        self.down_content_path = ft.Text(value=self.save_path,size=10,overflow=ft.TextOverflow.ELLIPSIS,max_lines=1)
        
        self.down_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Row([ft.Text(value="Change Path: "),
                            self.down_content_path]),      
                            ft.IconButton(
                                icon=ft.Icons.FOLDER,
                                icon_color="white70",
                                icon_size=18,
                                bgcolor="#242830",
                                width=32,
                                height=32,
                                on_click=self._select_folder
                            )
                        ],alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(value="Change Resolution: "),
                            ft.RadioGroup(
                                content=ft.Column(
                                    controls=[
                                        ft.Row(
                                    controls=[ft.Radio(label=x, value=x[:-1], scale=0.9, label_style=ft.TextStyle(size=13)) 
 for x in (self.video_info.available_qualities[:5] if len(self.video_info.available_qualities) > 5 else self.video_info.available_qualities)],
                                    wrap=True,
                                    run_spacing=10,
                                    spacing=10,
                                    expand=True
                                         ),
                                        ft.Row(
                                            controls=[ft.Radio(label=x, value=x[:-1]) for x in self.video_info.available_qualities[5:]] if self.video_info.available_qualities else [],
                                        )
                                    ]
                                ),value=self.resolutions, on_change=self._update_resolutions
                            )               

                        ]
                    )

                ],spacing= 5
            ),
            opacity=0,
            visible= False,
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            #clip_behavior=ft.ClipBehavior.HARD_EDGE
        )
        
        self.content = ft.Column(
            controls=[
                ft.Row(
            controls=[
                ft.Container(
                    width=40,
                    height=40,
                    border_radius=8,
                    bgcolor="#000000",
                    border=ft.border.all(1, "white10"),
                    content=ft.Image(
                        src=self.video_info.thumbnail_url,
                        fit=ft.ImageFit.COVER
                    )
                ),
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                self.video_title,
                                self.pb_percent
                            ]
                        ),
                        self.pb,
                        ft.Row(
                            controls=[
                                self.download_speed,
                                ft.Container(expand=True),
                                self.left_time
                            ]
                        )
                    ],
                    spacing=6,
                    expand=True
                ),
                self.button,
                self.button_cancel,
                self.button_rm
            ],
            spacing=12
        ),
        self.down_content
        
            ]
        )

    async def start_download(self, e):
        if self.status == "downloading":
            return
        
        print(f"🎬 {self.video_info.title} indiriliyor...")
        
        # UI'ı indirme moduna geçir
        self.status = "downloading"
        self.button.visible = False
        self.button_cancel.visible = True
        self.pb.value = 0
        self.pb_percent.value = "0%"
        self.video_title.value = f"({self.resolutions}p) "+self.video_info.short_title
        self.video_title.color = "white"

        self.height = 75
        self.down_content.visible = False
        self.down_content.opacity = 0
        self.update()

        try:
            result = await self.downloader.download(
                video_id=self.video_id,
                url=self.video_info.url,
                save_path=self.save_path,
                resolution=self.resolutions,
                progress_callback=self.progress_callback
            )

            if result == "Success":
                self.status = "completed"
                self.video_title.value = f"✓ {self.video_title.value}"
                self.video_title.color = "#10B981"
                self.pb.value = 1
                self.pb.color = "#10B981"
                self.pb_percent.value = "100%"
                self.pb_percent.color = "#10B981"
                self.download_speed.value = "Completed"
                self.left_time.value = "Done!"
                self.left_time.color = "#10B981"
                self.button_cancel.visible = False
                self.button.visible = False
                self.button_rm.visible = True
                print(f"✅ {self.video_info.title} tamamlandı!")
            
            elif result == "Cancelled":
                self.status = "cancelled"
                self.video_title.value = f"✗ {self.video_title.value}"
                self.video_title.color = "#F59E0B"
                self.download_speed.value = "Cancelled"
                self.left_time.value = ""
                self.button.visible = True
                self.button_cancel.visible = False
                self.button_rm.visible = True
                print(f"⚠️ {self.video_info.title} iptal edildi")
            
            else:
                self.status = "error"
                self.video_title.value = f"✗ {self.video_title.value}"
                self.video_title.color = "#EF4444"
                self.download_speed.value = f"Error: {result[:20]}"
                self.left_time.value = ""
                self.button.visible = True
                self.button_cancel.visible = False
                self.button_rm.visible = True
                print(f"❌ {self.video_info.title} hata: {result}")

        except Exception as ex:
            self.status = "error"
            self.video_title.value = f"✗ ({self.resolutions}p) {self.video_info.short_title}"
            self.video_title.color = "#EF4444"
            self.download_speed.value = f"Exception: {str(ex)[:20]}"
            self.button.visible = True
            self.button_cancel.visible = False
            print(f"❌ Exception: {self.video_info.title}: {str(ex)}")

        finally:
            self.update()

    async def cancel_download(self, e):
        # Hemen UI'ı güncelle
        self.status = "cancelling"
        self.video_title.value = f"⏸({self.resolutions}p) {self.video_info.short_title}"
        self.video_title.color = "#F59E0B"
        #self.button_cancel.disabled = True
        self.download_speed.value = "Cancelling..."
        self.update()
        
        # Arka planda iptal et
        try:
            await self.downloader.cancel(self.video_id)
        except Exception as ex:
            print(f"Cancel error: {ex}")
        
        # İptal tamamlandı
        self.status = "cancelled"
        self.button_cancel.visible = False
        self.button.visible = True
        self.button.icon = ft.Icons.REFRESH
        self.update()
        print(f"🛑 {self.video_info.title} iptal edildi")

    async def remove_from_queue(self, e):
        if self.status == "downloading":
            try:
                await self.downloader.cancel(self.video_id)
            except Exception as e:
                print(f"errror {e}")
                print(f"🛑 {self.video_info.title} iptal denedik bir şeyler")
        
        
            await self.queue_ref.remove_task(self.video_id)

    def progress_callback(self, data):
        """
        CRITICAL FIX: self.page yerine try-except kullan
        Thread-safe güncelleme garantisi
        """
        try:
            # İndirme aktif değilse güncelleme yapma
            if self.status not in ["downloading", "cancelling"]:
                return
            
            percentage = data.get('percentage', 0)
            speed = data.get('speed', 0) / 1024 / 1024  # Bytes to MB
            eta = data.get('eta', 0)

            # Progress bar güncelle
            self.pb.value = min(percentage / 100.0, 1.0)
            self.pb_percent.value = f"{int(percentage)}%"

            # Hız göster
            if speed > 0:
                self.download_speed.value = f"{speed:.2f} MB/s"
            
            # Kalan süre
            if eta > 0:
                minutes, seconds = divmod(int(eta), 60)
                if minutes > 0:
                    self.left_time.value = f"{minutes}m {seconds}s left"
                else:
                    self.left_time.value = f"{seconds}s left"

            # CRITICAL: page kontrolü YOK, direkt update()
            # Flet async event loop içinde olduğumuz için güvenli
            self.update()
            
        except Exception as e:
            # Hataları logla ama UI'ı bloklama
            print(f"⚠️ Progress callback error: {e}")
            pass
    
    def _on_hover(self,e):
        
        if e.data == "true" and self.status is "waiting":
            self.height = 200
            self.down_content.opacity = 1
            
            self.down_content.visible = True
        else:
            self.height = 75
            self.down_content.visible = False
            self.down_content.opacity = 0

        
        self.update()
        
    def _file_picker(self,e:ft.FilePickerResultEvent):
        if e.path:
            self.save_path = e.path
            self.down_content_path.value = e.path
        
        self.update()
    
    def _select_folder(self,e): self.file_picker.get_directory_path()

    def _update_resolutions(self,e): 
        self.resolutions = e.control.value
        self.video_title.value = f"({self.resolutions}p) "+self.video_info.short_title
        self.update()

