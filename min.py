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
    term_size = shutil.get_terminal_size()
    chars_w, chars_h = term_size.columns, term_size.lines
    # vibe coding solution
    px_width = chars_w * 8
    px_height = chars_h * 16
    img_w, img_h = image.size
    scale = min(px_width / img_w, px_height / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    resized = image.resize((new_w, new_h))

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        # yep, image to sixel, that simple and silly
        resized.save(tmp.name, format="PNG")
        subprocess.run(["img2sixel", tmp.name])
        os.unlink(tmp.name)


def pdf_viewer(stdscr, pdf_path, dpi=300):
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.clear()
    terminal_chars = os.get_terminal_size()
    terminal_px = (terminal_chars.columns * 8, terminal_chars.lines * 16)
    images = convert_from_path(pdf_path, dpi=dpi)
    total_pages = len(images)
    if total_pages == 0:
        stdscr.addstr(0, 0, "No pages found.")
        stdscr.getch()
        return

    current_page = 0
    needs_refresh = True

    def reload_pdf():
        nonlocal images, total_pages, needs_refresh
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
            total_pages = len(images)
            needs_refresh = True
        except:
            pass

    event_handler = PDFChangeHandler(on_change_callback=reload_pdf)
    observer = Observer()
    observer.schedule(
        event_handler,
        path=os.path.dirname(os.path.abspath(pdf_path)) or ".",
        recursive=False,
    )
    observer.start()
    try:
        while True:
            if needs_refresh:
                stdscr.clear()
                stdscr.addstr(
                    0,
                    0,
                    f"Page {current_page + 1}/{total_pages} — ←/→ or p/n to flip, q to quit\n",
                )
                stdscr.refresh()
                display_sixel(images[current_page])
                needs_refresh = False

            try:
                key = stdscr.getch()
                if key == -1:
                    time.sleep(0.1)
                    continue
                elif key in [ord("q"), ord("Q")]:
                    break
                elif key in [ord("n"), curses.KEY_RIGHT]:
                    if current_page < total_pages - 1:
                        current_page += 1
                        needs_refresh = True
                elif key in [ord("p"), curses.KEY_LEFT]:
                    if current_page > 0:
                        current_page -= 1
                        needs_refresh = True
            except curses.error:
                pass
    finally:
        observer.stop()
        observer.join()


def main():
    if len(sys.argv) < 2:
        print("Usage: python min.py <file.pdf>")
        return

    pdf_file = sys.argv[1]
    curses.wrapper(pdf_viewer, pdf_file)


if __name__ == "__main__":
    main()
