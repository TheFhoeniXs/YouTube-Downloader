import flet as ft
from ui.components import DownloadSection,CurrentSelection,DownloadQueue
from models.downloader import RobustDownloader


def main(page: ft.Page):
    page.title = "Youtube_downlaoder"
    downloder = RobustDownloader(3)
    dwn = DownloadQueue(downloader=downloder,save_path="downloads")
    down_section = DownloadSection(dwn.add_video)
    curr_selection = CurrentSelection()
    down_section.subscribe(curr_selection)

    page.add(
       down_section,
       dwn,
       curr_selection,
       
    )

if __name__ == "__main__":
    ft.app(main)
