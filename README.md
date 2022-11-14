# boibox 🐍📦

> _**Boiga**_ is a large genus of rear-fanged, mildly venomous snakes, known commonly as cat-eyed snakes or simply **cat
snakes**

Python tool using asynchronous web requests to manage files on [catbox.moe](https://catbox.moe).

## Installation

```bash
pip install boibox
```

## Features

### Upload

Upload a space-separated list of files from your computer to catbox. Optionally provide your userhash to associate
uploads with your account and allow them to be deleted later. See more in the [Delete](#delete) documentation below.

Usage:

```bash
> boibox upload image.png video.mp4 readme.txt
image.png -> https://files.catbox.moe/us8ulr.png
video.mp4 -> https://files.catbox.moe/qoqoku.mp4
readme.txt -> https://files.catbox.moe/834wl6.txt
```

### Download

Download a space-separated list of filenames or URLs from `files.catbox.moe`. Outputs to the current directory by
default, but this can be overriden with the `-destination` flag.

Usage:

```bash
> boibox download -destination Downloads us8ulr.png https://files.catbox.moe/qoqoku.mp4 834wl6.txt
Downloads/us8ulr.png
Downloads/qoqoku.mp4
Downloads/834wl6.txt
```

### Delete

Deletes a space-separated list of filenames or URLs from `files.catbox.moe`. Requires `-userhash` to be provided or
the `USERHASH` environment variable to be set. Your userhash can be found on
the [Manage Account page at catbox](https://catbox.moe/user/manage.php). Your userhash must be specified on uploads to
make them deletable.

Usage:

```bash
> boibox delete -userhash 2ab3bc08105ba7c171838f420 us8ulr.png https://files.catbox.moe/qoqoku.mp4 834wl6.txt
Files successfully deleted.
```
