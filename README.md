# .github

Organization-wide files for [The AI Learning Hub](https://github.com/the-ai-learning-hub).

The page you see on the organization's GitHub profile is [`profile/README.md`](profile/README.md). This file only describes the repository.

## What's here

| Path | What it is |
| :-- | :-- |
| [`profile/README.md`](profile/README.md) | The organization's public profile page |
| [`profile/assets/`](profile/assets) | The SVG artwork on that page, in a light and a dark version each. Generated, so don't edit by hand |
| [`scripts/build_profile_assets.py`](scripts/build_profile_assets.py) | The list of lessons. Builds every file in `profile/assets/` and the lesson sections of `profile/README.md` |
| [`LICENSE`](LICENSE) | MIT License |

## Adding a lesson to the profile

1. Add the lesson at the end of `LESSONS` at the top of [`scripts/build_profile_assets.py`](scripts/build_profile_assets.py). Copy an existing entry and change it; the comment above `LESSONS` explains every field. The colour is optional: lessons take teal, orange, purple, blue, coral and gold in order.
2. Run:

   ```bash
   uv run scripts/build_profile_assets.py
   ```

   This does everything else:
   - the network in the hero gains a layer (it fits at least six lessons);
   - the new station is drawn in light and dark, and the "next station" moves one number up;
   - in [`profile/README.md`](profile/README.md), the stations under **The path** and the table below them are rewritten from `LESSONS`.
3. Optional: if the lesson teaches how to answer one of the questions in **Why learn the basics…**, add a link to it in that table by hand.
4. Commit and push (see below).

```bash
git add README.md profile/ scripts/build_profile_assets.py
git commit -m "Add lesson 03 to the profile"
git push origin main
```

Everything in `profile/README.md` between `<!-- path:start -->` / `<!-- path:end -->` and `<!-- table:start -->` / `<!-- table:end -->` is overwritten on each run, so don't edit those parts by hand. The rest of the file is yours to edit.

To change the "next station" wording, edit `NEXT` in the script. To change the slogan, title or subtitle in the hero, edit the `hero()` function. Removing a lesson from `LESSONS` also removes its images.

The script downloads Bricolage Grotesque and JetBrains Mono (both SIL OFL) on its first run, caches them in `scripts/.cache/` (ignored by Git), and embeds only the characters each image uses, so the SVGs look identical everywhere and stay small.

## How the profile page is built

From top to bottom, [`profile/README.md`](profile/README.md) has:

1. **Hero** (`hero-*.svg`): the name, a one-line promise, `>>> understand(every_line_you_run)`, and the curriculum drawn as a neural network.
2. **The path** (`lesson-*.svg`): one clickable "station" per lesson on a dotted track, like a metro map. Each station shows a line of code typical of that lesson and two facts about it. The last station (`lesson-next-*.svg`) is dashed and announces the lesson being built. A table below links to the slides, repository and Colab of each lesson.
3. **Why learn the basics if AI can write the code?** (`notebook-*.svg`): a notebook cell where an agent writes code and *you* understand it, followed by the "before you press Enter" checklist from Lesson 01, with each question linked to the slide that answers it.
4. **Start in a minute**, **Help make it better** and the licence line, in plain Markdown.

## Design notes

- **The curriculum is a neural network.** In the hero, each lesson is a layer, the dashed layer is the lesson being built, and the last node is *You*. A signal runs through it every seven seconds; it stays still for anyone with reduced motion turned on. It is the only animation on the page.
- **Colours come from the lessons.** The three accent colours are the Palmer Penguins species colours (Adélie, Chinstrap, Gentoo) from the dataset used in Lesson 01, set on polar-night and ice backgrounds: teal for 00, orange for 01, purple for 02.
- **Light and dark.** Every image is served with `<picture>` and `prefers-color-scheme`, so it matches the viewer's GitHub theme. GitHub's mobile apps always show the light version.
- **Absolute image URLs.** Images point to `https://raw.githubusercontent.com/the-ai-learning-hub/.github/main/profile/assets/…`, because relative paths are not reliable on an organization profile. This means a new or changed image only shows up on the profile **after it is pushed to `main`**.
- **No external image services.** Everything is in this repository, so the page can't break because a third-party badge or banner service goes down.

## Previewing locally

Open any file in `profile/assets/` in a browser to see it, animation included. To see the whole page, use VS Code's Markdown preview, but note it loads the images from `main`, so it shows your new artwork only after you push.
