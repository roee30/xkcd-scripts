from pathlib import Path
import json, requests, asyncio, aiofiles, aiohttp, cv2, numpy as np

sem = asyncio.Semaphore(1024)


async def download_file(url, base=Path(".")):
    local_filename = url.split("/")[-1]
    file = base / local_filename
    done_path = file.with_name(f"{file.stem}-done.json")
    if done_path.exists():
        print(url, "exists")
        return
    async with sem, aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            r.raise_for_status()
            with open(file, "wb") as f:
                async for chunk in r.content.iter_any():
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    # if chunk:
                    f.write(chunk)
    print(url, "done")
    done_path.write_text("true")
    return local_filename


locations = json.loads(Path("locations.json").read_text())
TILE_SIZE = 1024


def walk(base):
    for name, location in locations.items():
        for i in range(location["height"] // TILE_SIZE):
            for j in range(location["width"] // TILE_SIZE):
                yield download_file(
                    f"https://xkcd.com/2712/tile/{name}_{i}_{j}.png", base
                )


async def download_all():
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    base = Path("tiles")
    base.mkdir(parents=True, exist_ok=True)
    await asyncio.wait(list(walk(base)))


def image_key(name, x, y):
    return f"tiles/{name}_{x}_{y}.png"

def stitch():
    base = Path("locations")
    base.mkdir(exist_ok=True, parents=True)
    for name, location in locations.items():
        im = np.hstack(
            [
                np.vstack(
                    [
                        cv2.imread(image_key(name, i, j))
                        for j in range(location["height"] // TILE_SIZE)
                    ]
                )
                for i in range(location["width"] // TILE_SIZE)
            ]
        )
        out = str(base / f"{name}.png")
        print(out)
        cv2.imwrite(out, im)


def main():
    asyncio.run(download_all())
    stitch()


if __name__ == "__main__":
    main()
