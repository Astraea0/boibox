import argparse
import asyncio
import aiohttp
import os
from pathlib import Path
from typing import List
from tqdm import tqdm


class CBManager:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.session.close()

    async def upload(self, file, user_hash):
        async with self.session.post('https://catbox.moe/user/api.php', data={
            'reqtype': 'fileupload',
            'userhash': user_hash,
            'fileToUpload': file
        }) as r:
            return file.name, await r.text()

    async def delete(self, urls: List[str], user_hash):
        url_list = " ".join(url.removeprefix("https://files.catbox.moe/") for url in urls)
        async with self.session.post('https://catbox.moe/user/api.php', data={
            'reqtype': 'deletefiles',
            'userhash': user_hash,
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


def valid_dir(path):
    path = Path(path)
    if path.is_dir():
        return path
    else:
        raise argparse.ArgumentTypeError(f"Invalid directory: {path}")


async def async_main():
    parser = argparse.ArgumentParser(description="manage files on catbox")
    subparsers = parser.add_subparsers(dest='command', required=True, title='subcommands')
    upload_parser = subparsers.add_parser("upload")
    upload_parser.add_argument("filename", nargs="+", type=argparse.FileType('rb'), help='file(s) to upload')
    user_hash = os.getenv("USERHASH", default="")
    upload_parser.add_argument("-userhash", default=user_hash, help='userhash from https://catbox.moe/user/manage.php')
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("url", nargs="+", help='url of file(s) to delete')
    delete_parser.add_argument("-userhash", default=user_hash, required=not bool(user_hash),
                               help='userhash from https://catbox.moe/user/manage.php')
    download_parser = subparsers.add_parser("download")
    download_parser.add_argument("url", nargs="+", help='url of file(s) to download')
    download_parser.add_argument("-destination", default=".", metavar="DIR", type=valid_dir, help='output directory')
    args = parser.parse_args()

    async with CBManager() as cb_manager:
        if args.command == "upload":
            for coro in tqdm(asyncio.as_completed([cb_manager.upload(file, args.userhash) for file in args.filename]), total=len(args.filename)):
                filename, output = await coro
                tqdm.write(f'{filename} -> {output}')
        elif args.command == "download":
            for coro in tqdm(asyncio.as_completed([cb_manager.download(url, args.destination) for url in args.url]), total=len(args.url)):
                tqdm.write(str(await coro))
        elif args.command == "delete":
            print(await cb_manager.delete(args.url, args.userhash))


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
