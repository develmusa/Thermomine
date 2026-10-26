# Marketing brief: aquarium mine thermometer

## Target customer

**Primary: the themed-tank hobbyist.** Usually 25–45, more often male. Keeps a tropical community or planted tank (60–200 L).
- **Buys:** statement decor such as shipwrecks, ruins and "military" pieces, and refreshes the decor every 1–3 years.
- **Trend:** LED-lit decor is growing faster than plain resin ornaments.
- **Wants from a thermometer** (from reviews): readable from across the room, accurate, and nothing that falls off the glass.

**Secondary: gift buyers.** Partners, friends or family shopping for someone who keeps a tank: birthdays, Christmas, Father's Day.

Evidence is thin: small, older surveys and market summaries. Validate with a test ad, a pre-order page or feedback from a club or forum before investing in stock.

## Positioning

> **A centrepiece that tells you the water temperature from across the room.**

Decor first, gadget second. The temperature is shown as a glow colour, so there's no display to squint at.

## Key messages (shop listing bullets)

1. **Temperature at a glance:** green when it's right, blue when it's too cold, red when it's too warm.
2. **Made to stay in the tank:** the only parts in the water are a sealed LED and a stainless probe, and all the electronics stay outside the tank.
3. **Twist-lock bayonet cap:** open it for cleaning, no tools needed.
4. **Set your own range:** the defaults are 24–27 °C (tropical). <!-- needs a way to change it without code before launch -->
5. **USB-C powered,** with a power supply included.

## Shots

| File | Use |
|---|---|
| `01_hero_aquarium.png` | Banner, social posts, ad creatives |
| `02_glance_triptych.png` | Listing image #2: explains the feature without words |
| `03_packshot_white.png` | Marketplace main image (white background) |

All renders come from `marketing_scenes.blend` (scenes *Marketing* and *Packshot*). To re-render:
`blender -b --factory-startup marketing_scenes.blend --python render_shots.py`

## Product changes the renders assume

- **Dyed-black finish on the outside, white on the inside.** A black interior absorbs the LED light and makes the glow weak, so dye only the outside or paint the inside white.
- **The colour range can be changed without editing code.** The listing bullet promises it, and the current firmware has the range hard-coded.

## Before you publish

- **Label the images as product renders** until you have photos of the real product. That matters for consumer protection rules, and buyers notice.
- **Check legal requirements before selling:** CE, ElektroG/WEEE registration, LUCID packaging registration and the product safety regulation (GPSR). See the earlier notes.
