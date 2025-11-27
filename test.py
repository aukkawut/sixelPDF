import curses
from pdf2image import convert_from_path
import tempfile
import subprocess
import os
import sys
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class PDFChangeHandler(FileSystemEventHandler):
    def __init__(self, on_change_callback):
        self.on_change_callback = on_change_callback

    def on_modified(self, event):
        if event.src_path.endswith(".pdf"):
            self.on_change_callback()


def display_sixel(image):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        image.save(tmp.name, format="PNG")
        subprocess.run(["img2sixel", tmp.name])
        os.unlink(tmp.name)


def get_terminal_pixel_size():
    t = shutil.get_terminal_size()
    return t.columns * 8, t.lines * 16


def render_page(pdf_path, page_index, dpi):
    return convert_from_path(
        pdf_path,
        dpi=dpi,
        first_page=page_index + 1,
        last_page=page_index + 1
    )[0]


def pdf_viewer(stdscr, pdf_path, base_dpi=120):
    curses.curs_set(0)
    stdscr.nodelay(False)
    zoom = 1.0
    pages = convert_from_path(pdf_path, dpi=1)
    total_pages = len(pages)
    current_page = 0

    offset_x = 0
    offset_y = 0
    zoomed_image = None

    def rerender():
        nonlocal zoomed_image, offset_x, offset_y

        target_dpi = max(20, int(base_dpi * zoom))
        zoomed_image = render_page(pdf_path, current_page, target_dpi)

        term_w, term_h = get_terminal_pixel_size()
        img_w, img_h = zoomed_image.size

        if img_w <= term_w:
            offset_x = 0
        else:
            offset_x = max(0, min(offset_x, img_w - term_w))

        if img_h <= term_h:
            offset_y = 0
        else:
            offset_y = max(0, min(offset_y, img_h - term_h))

    def redraw():
        term_w, term_h = get_terminal_pixel_size()
        img_w, img_h = zoomed_image.size

        right = min(offset_x + term_w, img_w)
        bottom = min(offset_y + term_h, img_h)

        tile = zoomed_image.crop((offset_x, offset_y, right, bottom))

        stdscr.clear()
        #stdscr.addstr(
        #    0, 0,
        #    f"Page {current_page+1}/{total_pages}  zoom={zoom:.2f}  off=({offset_x},{offset_y})"
        #)
        stdscr.refresh()
        display_sixel(tile)

    def reload_pdf():
        pass  

    handler = PDFChangeHandler(on_change_callback=reload_pdf)
    observer = Observer()
    observer.schedule(handler, os.path.dirname(os.path.abspath(pdf_path)) or ".", recursive=False)
    observer.start()

    rerender()
    redraw()

    try:
        while True:
            key = stdscr.getch()
            if key == -1:
                time.sleep(0.05)
                continue

            term_w, term_h = get_terminal_pixel_size()
            img_w, img_h = zoomed_image.size

            # Quit
            if key in (ord("q"), ord("Q")):
                break

            # Page flipping with ./, ONLY
            if key == ord("."):
                if current_page < total_pages - 1:
                    current_page += 1
                    offset_x = offset_y = 0
                    rerender()
                    redraw()
                continue

            if key == ord(","):
                if current_page > 0:
                    current_page -= 1
                    offset_x = offset_y = 0
                    rerender()
                    redraw()
                continue

            # Zoom
            if key in (ord("+"), ord("=")):
                zoom *= 1.25
                rerender()
                redraw()
                continue

            if key in (ord("-"), ord("_")):
                zoom = max(0.10, zoom / 1.25)
                rerender()
                redraw()
                continue

            # Scroll up/down/left/right in viewport
            if key == curses.KEY_UP:
                offset_y = max(0, offset_y - 120)
                redraw()
                continue

            if key == curses.KEY_DOWN:
                offset_y = min(max(0, img_h - term_h), offset_y + 120)
                redraw()
                continue

            if key == curses.KEY_LEFT:
                offset_x = max(0, offset_x - 120)
                redraw()
                continue

            if key == curses.KEY_RIGHT:
                offset_x = min(max(0, img_w - term_w), offset_x + 120)
                redraw()
                continue

    finally:
        observer.stop()
        observer.join()


def main():
    if len(sys.argv) < 2:
        print("Usage: sixelPDF file.pdf")
        return
    curses.wrapper(pdf_viewer, sys.argv[1])


if __name__ == "__main__":
    main()
