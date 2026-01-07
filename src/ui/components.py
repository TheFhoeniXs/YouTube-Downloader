from datetime import datetime
import flet as ft
from .style import AppColors
from models.validators import is_youtube_link_checker, get_video_info
from models.video_info import VideoInfo
from abc import ABC, abstractmethod
from models.downloader import RobustDownloader
from typing import Callable
import asyncio

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
        self.old_url:str = ""

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

        self.paste_btn = ft.TextButton(
            "PASTE",
            style=ft.ButtonStyle(
                color="white60",
                bgcolor="white10",
                padding=ft.padding.symmetric(horizontal=16, vertical=8)),
                on_click=self.paste_from_clipboard)

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
                                        self.paste_btn
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
        
    
    async def _url_input_blur(self,e):
        if not e.control.value: return
        if self._check_url_changed(e.control.value):
            await self._validate_and_fetch_video_info(e.control)

    async def _validate_and_fetch_video_info(self,e):
        self.url_input.read_only = True
        url = e.value.strip()

        if not is_youtube_link_checker(url=url):
            e.error_text = "❌ Invalid YouTube URL"
            e.border_color = ft.Colors.RED
            self.download_btn.bgcolor = AppColors.PASSİVE
            self.download_btn_is_active = False
            self.update()
            return
        self.format_dropdown.options = []
        e.error_text = None
        e.border_color = ft.Colors.BLUE
        self.url_input.read_only = False

        self._loading_state()

        try:
            print(f"🔍 Fetching video info for: {url}")
            video_info = await get_video_info(url=url)
            self._succes_state(video_info=video_info)
        except Exception as e:
            print(f"❌ Error: {e}")
            self._error_state(str(e))
        finally:
            self.url_input.read_only = False
            
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
        #print(f"✅ Video found: {video_info.title}")
        
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
            self.url_input.value = None
            self.url_input.read_only = False
            self.update()
    
    async def paste_from_clipboard(self,e):
        if self.page:
            clipboard_data = await self.page.get_clipboard_async()
            if clipboard_data:
                self.url_input.value = clipboard_data
                if self._check_url_changed(self.url_input.value):
                    await self._validate_and_fetch_video_info(self.url_input)
        self.update()

    def _check_url_changed(self,new_url:str):
        if new_url == "" or new_url == None:
            return False
        else: 
            if new_url.strip() == self.old_url:
                return False
            else: 
                self.old_url = new_url.strip()
                return True
            
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
       self.file_picker
       self.queue_column = ft.Column(
           expand=True,
           spacing=10,
           scroll=ft.ScrollMode.ALWAYS,
           controls=[]
       )
       self.max_concurrent = ft.TextField(
                hint_text="3/20",
                hint_style=ft.TextStyle(color="white20", size=11),
                text_style=ft.TextStyle(color="white40", size=11, weight=ft.FontWeight.BOLD),
                border_color="transparent",
                focused_border_color="transparent",
                bgcolor="transparent",
                content_padding=0,
                on_blur=self.set_Max_concurrent,
                expand=2
            )
       self.tasks = {}
       self.task_counter = 0
       self.defult_vid_path = ft.TextField(
                hint_text=self.save_path,
                hint_style=ft.TextStyle(color="white20", size=11),
                text_style=ft.TextStyle(color="white40", size=11, weight=ft.FontWeight.BOLD),
                border_color="transparent",
                focused_border_color="transparent",
                bgcolor="transparent",
                content_padding=0,
                on_blur=self._set_defult_path,
                expand=9

            )

       self.content = ft.Column(
            expand=True,
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("DOWNLOAD QUEUE", size=10, weight=ft.FontWeight.BOLD, color="white40"),
                        self.max_concurrent,
                        self.defult_vid_path,
                        ft.Container(expand=True),
                        ft.TextButton("CLEAR COMPLATED", style=ft.ButtonStyle(color=AppColors.PRIMARY, padding=0),on_click=self.remove_completed_tasks),
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
            self.task_counter -= 1
            self.update()
    
    async def remove_completed_tasks(self,e):
        tasks = {id: task for id, task in self.tasks.items() if task.status =="completed"}
        for i in tasks:
            await self.remove_task(i)

    async def set_Max_concurrent(self,e):
        value = e.control.value
        if value.isnumeric():
            await self.downloader.set_max_concurrent(int(value))
            self.max_concurrent.hint_text = value +"/20"
            self.max_concurrent.value = None
            
        self.update() 
    
    def _set_defult_path(self,e):
        value = e.control.value
        if value != "":
            self.save_path = value
            self.defult_vid_path.hint_text = value[:32] + "..." if len(value) > 32 else value
            self.defult_vid_path.value = None
        self.defult_vid_path.update()

class VideoTask(ft.Container):
    def __init__(self, video_id, downloader, video_info, save_path:str, resolution:str, queue_ref, file_picker:ft.FilePicker):
        super().__init__(
            bgcolor="#1A1D24",
            border_radius=12,
            border=ft.border.all(1, "white10"),
            padding=12,
            animate=ft.Animation(320, ft.AnimationCurve.EASE_OUT),
            on_hover=self._on_hover,
            height=75,
        )

        self.downloader = downloader
        self.video_info = video_info
        self.video_id = video_id   
        self.save_path = save_path
        self.resolutions = resolution
        self.queue_ref = queue_ref
        self.file_picker = file_picker
        self.file_picker.on_result = self._file_picker
        self.status = "waiting"
        
        # ✅ İptal kontrolü için flag
        self._is_cancelled = False
        
        # UI Components
        self.video_title = ft.Text(
            value=f"({self.resolutions}p) {self.video_info.short_title}", 
            size=11, 
            weight=ft.FontWeight.BOLD, 
            color="white",
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            tooltip=self.video_info.title,
            expand=True
        )
        self.pb_percent = ft.Text("0%", size=11, weight=ft.FontWeight.BOLD, color="#FF6A00")
        self.pb = ft.ProgressBar(value=0, height=4, border_radius=2, color="#FF6A00")
        self.download_speed = ft.Text("0.0 MB/s", size=9, weight=ft.FontWeight.W_500, color="white40")
        self.left_time = ft.Text("-- mins left", size=9, weight=ft.FontWeight.W_500, color="#FF6A00CC")
        
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
        
        self.down_content_path = ft.Text(
            value=self.save_path,
            size=10,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1
        )
        
        self.down_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Row([
                                ft.Text(value="Change Path: "),
                                self.down_content_path
                            ]),      
                            ft.IconButton(
                                icon=ft.Icons.FOLDER,
                                icon_color="white70",
                                icon_size=18,
                                bgcolor="#242830",
                                width=32,
                                height=32,
                                on_click=self._select_folder
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(value="Change Resolution: "),
                            ft.RadioGroup(
                                content=ft.Column(
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                ft.Radio(
                                                    label=x,
                                                    value=x[:-1],
                                                    scale=0.9,
                                                    label_style=ft.TextStyle(size=13)
                                                ) for x in (
                                                    self.video_info.available_qualities[:5] 
                                                    if len(self.video_info.available_qualities) > 5 
                                                    else self.video_info.available_qualities
                                                )
                                            ],
                                            wrap=True,
                                            run_spacing=10,
                                            spacing=10,
                                            expand=True
                                        ),
                                        ft.Row(
                                            controls=[
                                                ft.Radio(
                                                    label=x,
                                                    scale=0.9,
                                                    label_style=ft.TextStyle(size=13),
                                                    value=x[:-1]
                                                ) for x in self.video_info.available_qualities[5:]
                                            ] if len(self.video_info.available_qualities) > 5 else [],
                                        )
                                    ]
                                ),
                                value=self.resolutions,
                                on_change=self._update_resolutions
                            )               
                        ]
                    )
                ],
                spacing=5
            ),
            opacity=0,
            visible=False,
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
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
                                ft.Row(controls=[self.video_title, self.pb_percent]),
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
        
        #print(f"🎬 {self.video_info.title} indiriliyor...")
        
        # ✅ Flag'i sıfırla - RESTART için kritik
        self._is_cancelled = False
        
        # UI'ı indirme moduna geçir
        self.status = "downloading"
        self.button.visible = False
        self.button_cancel.visible = True
        self.button.icon = ft.Icons.PLAY_ARROW  # Reset icon
        self.pb.value = 0
        self.pb.color = "#FF6A00"
        self.pb_percent.value = "0%"
        self.pb_percent.color = "#FF6A00"
        self.video_title.value = f"({self.resolutions}p) {self.video_info.short_title}"
        self.video_title.color = "white"
        self.download_speed.value = "0.0 MB/s"
        self.left_time.value = "-- mins left"
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

            # ✅ İptal edildiyse UI güncellemesini atlat
            if self._is_cancelled:
                #print(f"⚠️ {self.video_info.title} - iptal edildi, sonuç işlenmiyor")
                return

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
                #print(f"✅ {self.video_info.title} tamamlandı!")
            
            elif result == "Cancelled":
                # Cancel_download zaten UI'ı güncelledi
                #print(f"⚠️ {self.video_info.title} iptal edildi (downloader response)")
                pass
            
            else:
                self.status = "error"
                self.video_title.value = f"✗ {self.video_title.value}"
                self.video_title.color = "#EF4444"
                self.download_speed.value = f"Error: {result[:20]}"
                self.left_time.value = ""
                self.button.visible = True
                self.button_cancel.visible = False
                self.button_rm.visible = True
                #print(f"❌ {self.video_info.title} hata: {result}")

        except Exception as ex:
            if not self._is_cancelled:
                self.status = "error"
                self.video_title.value = f"✗ ({self.resolutions}p) {self.video_info.short_title}"
                self.video_title.color = "#EF4444"
                self.download_speed.value = f"Exception: {str(ex)[:20]}"
                self.button.visible = True
                self.button_cancel.visible = False
                #print(f"❌ Exception: {self.video_info.title}: {str(ex)}")

        finally:
            if not self._is_cancelled:
                self.update()

    async def cancel_download(self, e):
        
        if self._is_cancelled or self.status != "downloading":
            return
        
        #print(f"🛑 İptal başlatılıyor: {self.video_info.title}")
        
        
        self._is_cancelled = True
        
        # 2. Status güncelle
        self.status = "cancelling"
        self.video_title.value = f"⏸ ({self.resolutions}p) {self.video_info.short_title}"
        self.video_title.color = "#F59E0B"
        self.download_speed.value = "Cancelling..."
        self.update()
        
        # 3. Downloader'ı iptal et
        try:
            await self.downloader.cancel(self.video_id)
        except Exception as ex:
            print(f"Cancel error: {ex}")
        
        # 4. Callback'lerin tamamen durması için bekle
        await asyncio.sleep(0.5)
        
        # 5. Final UI güncellemesi
        self.status = "cancelled"
        self.video_title.value = f"✗ ({self.resolutions}p) {self.video_info.short_title}"
        self.video_title.color = "#F59E0B"
        self.download_speed.value = "Cancelled"
        self.left_time.value = ""
        
        # Button state
        self.button_cancel.visible = False
        self.button.visible = True
        self.button.icon = ft.Icons.REFRESH
        self.button_rm.visible = True
        
        self.update()
        print(f"✅ İptal tamamlandı: {self.video_info.title}")

    async def remove_from_queue(self, e):
        if self.status == "downloading":
            self._is_cancelled = True
            try:
                await self.downloader.cancel(self.video_id)
                await asyncio.sleep(0.3)
            except Exception as ex:
                print(f"Remove cancel error: {ex}")
        
        await self.queue_ref.remove_task(self.video_id)

    def progress_callback(self, data):
        try:
            if self._is_cancelled or self.status not in ["downloading", "cancelling"]:
                return
            
            percentage = data.get('percentage', 0)
            speed = data.get('speed', 0) / 1024 / 1024
            eta = data.get('eta', 0)

            self.pb.value = min(percentage / 100.0, 1.0)
            self.pb_percent.value = f"{int(percentage)}%"

            if speed > 0:
                self.download_speed.value = f"{speed:.2f} MB/s"
            
            if eta > 0:
                minutes, seconds = divmod(int(eta), 60)
                if minutes > 0:
                    self.left_time.value = f"{minutes}m {seconds}s left"
                else:
                    self.left_time.value = f"{seconds}s left"

            if self.page:
                self.page.update()
            
        except Exception as e:
            pass
    
    def _on_hover(self, e):
        if e.data == "true" and self.status == "waiting":
            self.height = 200
            self.down_content.opacity = 1
            self.down_content.visible = True
        else:
            self.height = 75
            self.down_content.visible = False
            self.down_content.opacity = 0
        self.update()
        
    def _file_picker(self, e):
        if e.path:
            self.save_path = e.path
            self.down_content_path.value = e.path
        self.update()
    
    def _select_folder(self, e):
        self.file_picker.get_directory_path()

    def _update_resolutions(self, e):
        self.resolutions = e.control.value
        self.video_title.value = f"({self.resolutions}p) {self.video_info.short_title}"
        self.update()
