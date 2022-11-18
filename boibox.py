import argparse
import asyncio
import os
import sys
import errno
from pathlib import Path
from typing import List
from functools import singledispatchmethod

import aiohttp
from tqdm import tqdm


class CBManager:
    def __init__(self, user_hash):
        self.session = aiohttp.ClientSession()
        self.user_hash = user_hash

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.session.close()

    @singledispatchmethod
    async def upload(self, file):
        async with self.session.post('https://catbox.moe/user/api.php', data={
            'reqtype': 'fileupload',
            'userhash': self.user_hash,
            'fileToUpload': file
        }) as r:
            return file.name, await r.text()

    @upload.register
    async def _(self, file: str):
        async with self.session.post('https://catbox.moe/user/api.php', data={
            'reqtype': 'urlupload',
            'userhash': self.user_hash,
            'url': file
        }) as r:
            return file, await r.text()

    async def delete(self, urls: List[str]):
        url_list = " ".join(url.removeprefix("https://files.catbox.moe/") for url in urls)
        async with self.session.post('https://catbox.moe/user/api.php', data={
            'reqtype': 'deletefiles',
            'userhash': self.user_hash,
            'files': url_list
        }) as r:
            return await r.text()

    async def download(self, url: str, output_directory: Path):
        name = url.removeprefix("https://files.catbox.moe/")
        url = "https://files.catbox.moe/" + name

        filename = output_directory / name
        async with self.session.get(url) as r:
            r.raise_for_status()
            filename.write_bytes(await r.read())

        return filename


def valid_dir(path: str):
    path = Path(path)
    if path.is_dir():
        return path
    else:
        raise argparse.ArgumentTypeError(f"Could not find directory: {path}")


def valid_file_or_url(path: str):
    if path == '-':
        return sys.stdin

    try:
        return open(path, 'rb')
    except OSError as e:
        if e.errno in (errno.ENOENT, errno.EINVAL):
            # Check if it is a URL
            if path.lower().startswith('http'):
                return path
            else:
                raise argparse.ArgumentTypeError(f'Could not find file or URL: {path}')
        else:
            # It is some other kind of OS error. It cannot be opened, but it may still exist.
            raise argparse.ArgumentTypeError(f'Could not open file: {path}')


async def async_main():
    user_hash = os.getenv("USERHASH", default="")
    parser = argparse.ArgumentParser(description="manage files on catbox")
    subparsers = parser.add_subparsers(required=True, title='subcommands', metavar='<upload|download|delete>')
    upload_parser = subparsers.add_parser("upload", aliases=['u', 'up'], help='upload file(s) to catbox')
    upload_parser.add_argument("filename", nargs="+", type=valid_file_or_url, help='file(s) to upload')
    upload_parser.set_defaults(action='upload')
    upload_parser.add_argument("-userhash", default=user_hash, help='userhash from https://catbox.moe/user/manage.php')
    delete_parser = subparsers.add_parser("delete", aliases=['r', 'remove'], help='delete file(s) from catbox')
    delete_parser.add_argument("url", nargs="+", help='url of file(s) to delete')
    delete_parser.add_argument("-userhash", default=user_hash, required=not user_hash,
                               help='userhash from https://catbox.moe/user/manage.php')
    delete_parser.set_defaults(action='delete')
    download_parser = subparsers.add_parser("download", aliases=['d', 'down'], help='download file(s) from catbox')
    download_parser.add_argument("url", nargs="+", help='url of file(s) to download')
    download_parser.add_argument("-destination", default=".", metavar="DIR", type=valid_dir, help='output directory')
    download_parser.set_defaults(action='download')
    args = parser.parse_args()

    async with CBManager(getattr(args, 'userhash', user_hash)) as cb_manager:
        if args.action == "upload":
            for coro in tqdm(asyncio.as_completed(map(cb_manager.upload, args.filename)), total=len(args.filename)):
                filename, output = await coro
                tqdm.write(f'{filename} -> {output}')
        elif args.action == "download":
            for coro in tqdm(asyncio.as_completed([cb_manager.download(url, args.destination) for url in args.url]),
                             total=len(args.url)):
                try:
                    tqdm.write(str(await coro))
                except aiohttp.ClientResponseError as e:
                    error = f'* Error while downloading {e.request_info.url}: {e.status} {e.message}'
                    tqdm.write(error, file=sys.stderr)
        elif args.action == "delete":
            print(await cb_manager.delete(args.url))


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
