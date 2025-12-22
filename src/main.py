import flet as ft
from ui.components import Download_Section,Current_Selection

def main(page: ft.Page):
    page.title = "Youtube_downlaoder"
    down_section = Download_Section()
    curr_selection = Current_Selection()
    down_section.subscribe(curr_selection)

    page.add(
       down_section,
       curr_selection
    )


ft.app(main)
