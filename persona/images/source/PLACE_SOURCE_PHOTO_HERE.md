# Drop the source photo here

Save the original photo of the four badges/cards in this folder as:

    business_cards.jpg

Then from the repo root run:

    pip install pillow numpy scipy
    python scripts/split_business_cards.py \
        persona/images/source/business_cards.jpg \
        persona/images/cropped/

The script will write four files into `persona/images/cropped/`:

- `usi.jpg`
- `cigna.jpg`
- `hines.jpg`
- `fountain_health.jpg`

If auto-detection misses a card, the script writes a `crop_boxes.json`
next to the source. Adjust the four `[left, top, right, bottom]` boxes
in that file and re-run with `--manual`.
