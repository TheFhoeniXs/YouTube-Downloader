import flet as ft
from ui.components import DownloadSection,CurrentSelection,DownloadQueue
from models.downloader import RobustDownloader

def main(page: ft.Page):
    page.title = "Youtube_downlaoder"
    page.padding = 20
    
    downloder = RobustDownloader(3)
    down_queue = DownloadQueue(downloader=downloder,save_path="downloads")
    down_section = DownloadSection(down_queue.add_video)
    curr_selection = CurrentSelection()
    down_section.subscribe(curr_selection)
    
    # History Section
    history_section = ft.Column(
        controls=[
            ft.Text("HISTORY", size=10, weight=ft.FontWeight.BOLD, color="white40"),
            ft.Container(height=10),
            ft.Row(
                controls=[
                    ft.Container(
                        bgcolor="#1A1A1A",
                        border=ft.border.all(1, "white10"),
                        border_radius=12,
                        padding=12,
                        expand=True,
                        content=ft.Row([
                            ft.Container(width=40, height=40, bgcolor="white10", border_radius=8),
                            ft.Column([
                                ft.Text("Relaxing Nature 4K", size=12, color="white"),
                                ft.Text("1.2 GB • Yesterday", size=10, color="white40")
                            ], spacing=2)
                        ])
                    ),
                    ft.Container(
                        bgcolor="#1A1A1A",
                        border=ft.border.all(1, "white10"),
                        border_radius=12,
                        padding=12,
                        expand=True,
                        content=ft.Row([
                            ft.Container(width=40, height=40, bgcolor="white10", border_radius=8),
                            ft.Column([
                                ft.Text("Tech Talk Ep. 42", size=12, color="white"),
                                ft.Text("850 MB • 2 days ago", size=10, color="white40")
                            ], spacing=2)
                        ])
                    ),
                    ft.Container(
                        bgcolor="#1A1A1A",
                        border=ft.border.all(1, "white10"),
                        border_radius=12,
                        padding=12,
                        expand=True,
                        content=ft.Row([
                            ft.Container(width=40, height=40, bgcolor="white10", border_radius=8),
                            ft.Column([
                                ft.Text("Best Setup 2024", size=12, color="white"),
                                ft.Text("340 MB • 3 days ago", size=10, color="white40")
                            ], spacing=2)
                        ])
                    ),
                    ft.Container(
                        bgcolor="#1A1A1A",
                        border=ft.border.all(1, "white10"),
                        border_radius=12,
                        padding=12,
                        expand=True,
                        content=ft.Row([
                            ft.Container(width=40, height=40, bgcolor="white10", border_radius=8),
                            ft.Column([
                                ft.Text("Minimalist Art Docu", size=12, color="white"),
                                ft.Text("1.5 GB • 1 week ago", size=10, color="white40")
                            ], spacing=2)
                        ])
                    ),
                ],
                spacing=15,
                wrap=True
            )
        ]
    )
    
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
    
    page.add(main_content)

if __name__ == "__main__":
    ft.app(main)