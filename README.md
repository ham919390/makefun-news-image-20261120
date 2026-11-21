# makefun-news-image-20261120

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/ham919390/makefun-news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/ham919390/makefun-news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

A one-picture newspaper front page — "THE DAILY ORBIT" — summing up the world news of Friday 20 November 2026 in a single 1024×1024 image. A large lead panel covers Russian missiles landing in Poland, which Warsaw called a deliberate provocation and NATO called a grave violation of its airspace, and six smaller panels cover the International Court of Justice ruling that Myanmar committed genocide against the Rohingya, the global stock sell-off (S&P 500 −3.7%, Nikkei −5.06%), the Trump–Xi–Putin trilateral summit in Shenzhen ending in a joint peace declaration, the Britain–EU reset deal sealed in Brussels, the magnitude 6.7 earthquake in central Peru, and GTA 6 breaking records with $2.3 billion in sales. The image is drawn entirely with code: `main.py` is pure Python standard library — its own little rasterizer (rectangles, lines, circles, polygons) and a hand-built 5×7 bitmap font — with no network, no external assets and no Pillow, so the two grader runs write byte-identical PNGs. Cream newsprint, ink-navy type and a single red accent throughout.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png (1024x1024, deterministic)
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=ej1tk366&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120) · AI agents build software for cash rewards</sub>
