# sixelPDF

PDF rendering thingy for sixel terminals.

## Why?

Why not? I use `st` and `nvim` to work with latex, so yeah... I need side by side PDF rendering. Problem is, what we already have is either with kitty or is notorious (at least on my computer) to compile.

## What does this do?

Well, very basic stuff. As of right now, it can turn pages and hot reload (well, not really, you need to refresh it with some key). That is it. 

## Principle

So, we have PDF file, we read it, and we turn it into image file. Then, use `img2sixel`. Yes, I know. Silly. But it works, at least for my use case.

## Requirements

Obviously 2 things:
- python (with required libraries in `requirements.txt`) 
- sixel (with at least img2sixel executable)

And one optional thing:
- terminal with sixel support (well, you can technically run this on terminal without sixel support, just you know... duh)

By the way, this is tested on Linux (specifically, Gentoo Linux). Probably doesn't work well with Windows...

## How to use

```
python min.py <pdf_file>
```
Keybinding will be shown when you run. You can change it too (by modifying the code, of course). 
