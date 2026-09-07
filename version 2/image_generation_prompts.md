# High-Resolution Image Generation Prompts
The following prompts are carefully designed to generate photorealistic, cinematic, and extremely high-resolution (8K) assets for "Path to Moksha". Using these prompts in an AI image generator (such as Midjourney v6, DALL-E 3, or Stable Diffusion XL) will eliminate pixelation in full-screen mode and give the game a premium, modern AAA feel.

## 1. Background Environments
These should be generated in a 16:9 aspect ratio (e.g., `--ar 16:9` for Midjourney) to fill a standard widescreen monitor perfectly.

*   **`title_background.png`**
    *   **Prompt:** `Hyper-realistic cinematic landscape of a majestic ancient Indian Jain temple atop a serene mountain at sunrise. Breathtaking golden hour lighting, glowing mist rolling over the peaks, high-resolution 8k, Unreal Engine 5 render style, highly detailed architecture, spiritual and peaceful atmosphere, wide angle.`
*   **`level1_background.png`** (The Commute - Samsara)
    *   **Prompt:** `Hyper-realistic cinematic 16:9 wide-angle side-scrolling Toronto streetscape, single seamless cohesive image, bright sunny day with vivid blue sky and soft white cumulus clouds. Composed in clear parallel depth layers: FOREGROUND LAYER — wide two-lane asphalt road with white dashed lane markings, a concrete sidewalk with a metal TTC bus shelter bench and a red Canada Post mailbox, mature street trees with full green foliage, a classic black pole-mounted TTC sign (red-and-white Toronto Transit Commission logo) and a black street sign reading "Queen St. E. - Broadview". GROUND-FLOOR LAYER — a tightly packed continuous row of charming two-storey red-brick Victorian commercial buildings directly behind the sidewalk: "Toronto Pizza" with a red-and-white striped fabric awning, "City Bakery" with a blue-and-white striped awning, a "Grocery Market" with colourful produce bins outside, a "Bookshop" with a green sign, and a corner building with a TTC Subway entrance. SECOND DEPTH LAYER — directly behind the ground floor buildings, two-storey warm red-brick residential row houses with pitched roofs, double-hung sash windows, and brick chimneys visible above the shop rooflines. FAR BACKGROUND LAYER — fully crisp, sharp, and in perfect focus: tall glass and concrete mid-rise and high-rise office buildings with clearly visible window grids, and the iconic CN Tower with its distinctive pod and antenna rising sharply against a vivid bright blue sky, no atmospheric haze, no blur, no depth of field effect, all layers equally sharp. Unreal Engine 5 photorealistic rendering, 8K resolution, ultra-detailed brick textures, volumetric sunlight, no construction site, no orange barricades, no work zone signs, tack sharp throughout entire image, --ar 16:9`
*   **`level2_background.png`** (The Mountain Ascent)
    *   **Prompt:** `Hyper-realistic cinematic 16:9 side-scrolling 2D platformer game background. FLAT ORTHOGRAPHIC PLATFORMS WITH NATURAL DEPTH GRADIENT: horizontal jumping surfaces remain perfectly level, but background transitions GRADUALLY and SMOOTHLY from dark foreground to bright mountains—NO sudden cuts or hard edges. BOTTOM LAYER (0-15% of image) — dark, richly textured stone ledge running edge-to-edge, sharp detail, warm dark earth tones, moss-covered rocks, scattered tree roots creating visual interest but not breaking the horizontal plane. This is the darkest, sharpest zone. LOWER-MID PLATFORMS (15-38% of image) — massive healthy ancient tree trunks with flat top surfaces for jumping, dark gnarled bark with deep shadow detail, thick hanging vines, caves and rocky crevices, medium-dark earthy tones, crisp focus. GRADUAL CANOPY OPENING (38-62% of image) — forest becomes progressively lighter and more open as it recedes, vegetation slowly transitions from dense to sparser, large moss-covered boulders and rocky outcrops visible as platform surfaces, central waterfall dropping vertically with turquoise water, hanging lianas and ferns, tones brighten progressively from dark green to lighter warm gold. CRITICAL: canopy gradually opens upward, allowing glimpses of distant background, NOT a hard cut. BACKGROUND MOUNTAINS VISIBLE THROUGH CANOPY (62-100% of image) — towering mountain peaks becoming progressively more visible through gaps in the upper canopy, soft hazy silhouettes in pale golden tones, mountains appear to recede naturally into misty atmosphere, very light tones and soft details, NO abrupt crop or hard line where trees end. Smooth atmospheric haze creates sense of great distance. Living, healthy forest aesthetic throughout. Golden-hour volumetric sunlight rays, Unreal Engine 5 photorealistic style, 8K resolution, foreground sharpest/darkest, background softest/lightest, NO hard cuts or unnatural composition breaks, --ar 16:9`
*   **`level3_background.png`** (The Floating Sanctuary)
    *   **Prompt:** `Hyper-realistic cinematic landscape of a sacred floating island sanctuary in the sky. Ethereal waterfalls cascading into the abyss below, ancient white marble pillars, radiant divine lighting, high-resolution 8k, majestic, heavenly realm.`
*   **`level4_background.png`** (The Steps to Enlightenment)
    *   **Prompt:** `Hyper-realistic cinematic landscape of the steps to enlightenment. An impossibly high celestial staircase made of glowing, polished white marble extending upwards into a brilliant, warm golden sky, high-resolution 8k, divine, transcendent lighting, volumetric fog.`

## 2. Character Sprites
These should be generated on a clean white or transparent background so they can easily be cut out and used in `character_select.py` and the game engine.

*   **`player_boy.png`**
    *   **Prompt:** `High-resolution full body character concept art of a young Indian boy devotee on a spiritual pilgrimage. Wearing traditional clean saffron robes (dupatta), peaceful and determined expression, standing straight on a pure white background, cinematic studio lighting, 8k resolution, ultra-realistic cloth textures.`
*   **`player_girl.png`**
    *   **Prompt:** `High-resolution full body character concept art of a young Indian girl devotee on a spiritual pilgrimage. Wearing traditional clean white and saffron garments, peaceful and focused expression, standing straight on a pure white background, cinematic studio lighting, 8k resolution, ultra-realistic cloth textures.`
*   **`player_boy_bowing.png`** (Side view bowing pose for transition scenes)
    *   **Prompt:** `Side-profile 2D game character sprite of a young Indian boy devotee performing a deep devotional bow (Panchanga Pranam / prostration gesture). Wearing traditional clean saffron robes (dupatta), hands joined together in Namaste prayer extended forward, head bowed in reverence, side view facing right, isolated on pure white background, clean character art style, transparent PNG, 8K resolution, 2D platformer asset.`
*   **`player_girl_bowing.png`** (Side view bowing pose for transition scenes)
    *   **Prompt:** `Side-profile 2D game character sprite of a young Indian girl devotee performing a deep devotional bow (Panchanga Pranam / prostration gesture). Wearing traditional clean white and saffron garments, hands joined together in Namaste prayer extended forward, head bowed in reverence, side view facing right, isolated on pure white background, clean character art style, transparent PNG, 8K resolution, 2D platformer asset.`

## 3. Transition & Story Assets
These are used during level transitions and the final victory screen.

*   **`jsot_temple.png`**
    *   **Prompt:** `Hyper-realistic architectural photography of a pristine white marble Jain temple. Majestic intricately carved domes, wide angle, bright sunny day with clear blue sky, high-resolution 8k, incredibly detailed stonework, photorealistic.`
*   **`parshvanath.png`**
    *   **Prompt:** `Hyper-realistic divine portrait of Lord Parshvanath in deep meditation (Padmasana posture). A majestic, highly detailed seven-headed snake canopy protecting him from above, glowing ethereal aura, cinematic lighting, 8k resolution, serene and divine masterpiece.`
*   **`mahavir.png`**
    *   **Prompt:** `Hyper-realistic divine portrait of Lord Mahavir in deep meditation. Radiant golden aura emanating from behind him, sitting perfectly still on a majestic carved stone pedestal, peaceful expression, high-resolution 8k, spiritual lighting, photorealistic.`
*   **`adinath.png`**
    *   **Prompt:** `Hyper-realistic divine portrait of Lord Adinath (Rishabhanatha) in deep meditation. Long flowing hair resting gracefully over his shoulders, sitting in lotus position, radiant warm spiritual light illuminating him, high-resolution 8k, serene photographic masterpiece.`
*   **`digambar_garbhalaya.png`** (Victory Screen)
    *   **Prompt:** `Hyper-realistic interior of a sacred Digambar Jain Garbhalaya (inner sanctum). A majestic, perfectly smooth marble idol of a Tirthankara in deep meditation, lit softly by dozens of glowing traditional oil lamps (diyas). Warm golden reflections on the marble floors, deeply spiritual atmosphere, 8k resolution, dramatic cinematic lighting.`
*   **`temple_gate.png`** (Level 1 Goal - The Entrance to Sanctity)
    *   **Prompt:** `Hyper-realistic cinematic architectural close-up of a majestic Digamber Jain Temple gate, set on a city street corner, isolated against a transparent or clean studio background, front-on flat angle view for game sprite use. The gate is constructed from pure, luminous white Makrana marble, featuring an exquisite grand archway (Torana) with incredibly detailed hand-carved pillars depicting elephants, sacred kalash pots, and traditional geometric floral scrollwork. The heavy central door is made of dark aged teak wood, adorned with polished circular brass studs and a traditional golden lock. Ambient warm sunbeams strike the marble surface, highlighting the micro-textures of the stone. Ultra-detailed 8K resolution, photorealistic Unreal Engine 5 render, tack-sharp textures, architectural masterpiece, cinematic commercial rendering, AAA game art asset quality.`

*   **`monk_sprite.png`** (In-Game Monk / Guide NPC Character — replaces procedural drawing)
    *   **Save to:** `assets\images\items\`
    *   **Sprite size:** Approx. **76×110 pixels** in-game (the image will be auto-scaled, so generate at higher resolution for quality)
    *   **Prompt:** `Full-body 2D game sprite of a serene Digambara Jain monk seated in Padmasana (lotus meditation posture). Sky-clad (no clothing), warm dusky golden-brown skin tone, long matted hair (jata) piled atop his head, eyes gently closed in deep meditation. In his right hand rests a Picchi (peacock-feather fly-whisk) and beside him on the ground is a small wooden Kamandalu (water pot). The figure is illuminated by soft warm spiritual light from the upper-left. Style: high-resolution 2D game character art, painterly flat-shading, crisp clean outlines, vibrant warm saffron and golden tones, spiritual and dignified, transparent PNG background, no text, no background scene, isolated character only, 8K resolution quality, suitable for a 2D platformer game sprite.`

## 4. Box Item Icons (Bottom Band Shelf)
These are small 64×64 pixel icon images. Each must have a **transparent background** (PNG with alpha). The game draws the category-colored background tile automatically — the image should only show the item itself. Style: **flat spiritual icon art**, vivid colors, clear silhouette, thick outlines, no text or labels.
Save all icons to: `assets\images\items\`

### GOAL Items — displayed on Gold tile in-game

*   **`temple_key.png`**
    *   **Prompt:** `A single ornate golden temple key with a decorative lotus-shaped bow and intricate carved handle. The key looks ancient and sacred. Flat 2D icon art style, transparent background, 64x64 pixels, thick gold outline, bold vivid colors, no text, no background.`

*   **`akshat.png`**
    *   **Prompt:** `A small sacred mound of white cream-coloured rice grains (Akshat) presented on a lotus leaf. Looks spiritual and traditional. Flat 2D icon art style, transparent background, 64x64 pixels, thick outline, no text, no background.`

### SUPPORT Items — displayed on Green tile in-game

*   **`ttc_bus.png`**
    *   **Prompt:** `A red Toronto TTC city bus, front-facing view, small and cute cartoon icon. Flat 2D icon art style, transparent background, 64x64 pixels, bold outline, no text labels on the bus, no background.`

*   **`personal_car.png`**
    *   **Prompt:** `A modern silver or blue personal car, side view, cute and simple cartoon icon. Flat 2D icon art style, transparent background, 64x64 pixels, bold outline, no text, no background.`

*   **`ghanta.png`**
    *   **Prompt:** `A shiny traditional Jain temple bell (Ghanta) with a lotus-shaped handle, hanging position. Rich golden color, flat 2D icon art style, transparent background, 64x64 pixels, thick outlined style, no text, no background.`

*   **`lakshan_snake.png`**
    *   **Prompt:** `A coiled golden serpent (Dharanendra / Nagendra snake), sacred and dignified, depicted in a regal spiritual pose. Flat 2D icon art style, green and gold tones, transparent background, 64x64 pixels, no text, no background.`

*   **`chanvar.png`**
    *   **Prompt:** `A ceremonial Jain fan (Chanvar / Chauri) — a white yak-tail fan on a decorative gold handle used in Jain temple rituals. Flat 2D icon art style, cream and gold tones, transparent background, 64x64 pixels, no text, no background.`

*   **`lakshan_lion.png`**
    *   **Prompt:** `A majestic, regal golden lion head (Jain Lakshan symbol), facing forward, dignified and spiritual look. Flat 2D icon art style, warm golden tones, transparent background, 64x64 pixels, bold outline, no text, no background.`

*   **`lakshan_bull.png`**
    *   **Prompt:** `A sturdy, calm white bull (Nandi-style bull, Jain Lakshan symbol), side view. White and gold tones, sacred calm expression. Flat 2D icon art style, transparent background, 64x64 pixels, no text, no background.`

### DISTRACTION Items — displayed on Red tile in-game

*   **`mobile_phone.png`**
    *   **Prompt:** `A modern smartphone with a glowing screen showing social media notifications or a selfie camera icon. Looks like a distraction. Flat 2D icon art style, bright colors, transparent background, 64x64 pixels, bold outline, no text, no background.`

*   **`food.png`**
    *   **Prompt:** `A steaming bowl of delicious Indian street food (chaat or a bowl of rice with garnish). Looks tempting and warm. Flat 2D icon art style, transparent background, 64x64 pixels, no text, no background.`

*   **`movie_ticket.png`**
    *   **Prompt:** `A classic red-and-gold striped cinema movie ticket stub with a perforation line. Flat 2D icon art style, transparent background, 64x64 pixels, bold outline, no written text or words on the ticket, no background.`

*   **`friend.png`**
    *   **Prompt:** `A cheerful cartoon friend character — a simple smiling person with an outstretched hand waving, as if calling out to you. Flat 2D icon art style, warm skin tones, transparent background, 64x64 pixels, no text, no background.`

*   **`foe.png`**
    *   **Prompt:** `A scowling, menacing cartoon enemy character in dark red tones, pointing aggressively at the viewer. Flat 2D icon art style, transparent background, 64x64 pixels, bold outline, no text, no background.`

### NO EFFECT Items — displayed on Grey tile in-game

*   **`wrong_lakshan_bull.png`**
    *   **Prompt:** `A cartoon bull head in muted grey-brown tones with a large question mark floating above it, conveying confusion or a wrong symbol. Flat 2D icon art style, transparent background, 64x64 pixels, no text, no background.`

*   **`wrong_lakshan_lion.png`**
    *   **Prompt:** `A cartoon lion head in muted grey-brown tones with a large question mark floating above it, conveying confusion or a wrong symbol. Flat 2D icon art style, transparent background, 64x64 pixels, no text, no background.`

### Quick Reference — File Names

| Item Name | Category | File Name |
|---|---|---|
| Temple Key | Goal (Gold) | `temple_key.png` |
| Akshat | Goal (Gold) | `akshat.png` |
| TTC Bus | Support (Green) | `ttc_bus.png` |
| Personal Car | Support (Green) | `personal_car.png` |
| Ghanta | Support (Green) | `ghanta.png` |
| Lakshan (Snake) | Support (Green) | `lakshan_snake.png` |
| Chanvar | Support (Green) | `chanvar.png` |
| Lakshan (Lion) | Support (Green) | `lakshan_lion.png` |
| Lakshan (Bull) | Support (Green) | `lakshan_bull.png` |
| Mobile Phone | Distraction (Red) | `mobile_phone.png` |
| Food | Distraction (Red) | `food.png` |
| Movie Ticket | Distraction (Red) | `movie_ticket.png` |
| Friend | Distraction (Red) | `friend.png` |
| Foe | Distraction (Red) | `foe.png` |
| Wrong Lakshan (Bull) | No Effect (Grey) | `wrong_lakshan_bull.png` |
| Wrong Lakshan (Lion) | No Effect (Grey) | `wrong_lakshan_lion.png` |

> **NOTE:** If an image is missing, the game automatically shows the first letter of the item name inside the colored tile. You can add images one at a time.

## 5. Player Character Sprite Sheet (4-Directional & All Actions)
To replace the procedural drawing of the player character inside each level (the orange rect pilgrim) with the young Indian pilgrim boy (Shravak), you need a comprehensive 4-directional sprite sheet. 

Due to the constraints of AI image generators, the output must be run through a post-processing pipeline before importing it into the Pygame engine.

### Base Character Specifications
*   **Subject:** A young Indian boy pilgrim (Shravak), age 10-12, short neat black hair, warm brown skin tone, calm expression.
*   **Clothing:** Traditional white long-sleeve kurta, draped white dhoti (lower garment), brown leather sandals. A white diagonal shoulder dupatta (uttariya) wraps across his chest from left shoulder to right waist.
*   **Aesthetic:** Clean 2D flat-shaded game sprite, thin dark outline, vibrant colors, isolated on a pure transparent or solid white background. No gradient shadows.

---

### Part A: Strict Frame-Count Parity (The Animation Standard)
To ensure the game's animation system remains clean, you must enforce a **fixed frame count** for each animation type across all four directions:

| Animation | Frame Count | Description |
|---|---|---|
| **`idle`** | **4 frames** | Standing still, subtle breathing loop, gentle dupatta sway |
| **`walk`** | **6 frames** | Steady walking loop, alternating strides, arms swinging naturally |
| **`run`** | **6 frames** | Fast running loop, body leaning forward, arms pumping, robes fluttering |
| **`jump`** | **4 frames** | Crouch prepare (1) → Launch upward (2) → Peak float (3) → Transition to fall (4) |
| **`fall`** | **3 frames** | Descending downwards, hair/garments blowing upwards |
| **`stun`** | **2 frames** | Slouched body, head drooping, staggered dizzy loop |

---

### Part B: Directional Sprite Strips Prompts
Generate separate horizontal strips for each action and direction to achieve clean loops and avoid scale/lighting drift.

#### 1. Facing RIGHT (Side View)
*   **Idle (4 frames):** `A 4-frame idle animation horizontal sprite strip of a young Indian boy pilgrim in a white kurta and dhoti. Standing still, Facing RIGHT, subtle breathing loop, dupatta swaying. Pure white background, flat 2D vector art style, clean outlines, no shadows, no motion blur, --ar 16:9`
*   **Walk (6 frames):** `A 6-frame walking cycle horizontal sprite strip of a young Indian boy pilgrim in a white kurta and dhoti, Facing RIGHT, walking right with steady, alternating leg strides and swinging arms. Pure white background, flat 2D game asset, --ar 16:9`
*   **Run (6 frames):** `A 6-frame running cycle horizontal sprite strip of a young Indian boy pilgrim in a white kurta and dhoti, Facing RIGHT, running right with body leaning forward, arms pumping, white robes fluttering. Pure white background, flat 2D game asset, --ar 16:9`
*   **Jump (4 frames):** `A 4-frame jumping horizontal sprite strip of a young Indian boy pilgrim in a white kurta, Facing RIGHT. Frame 1: crouch launch. Frame 2: rising upward. Frame 3: peak of jump. Frame 4: top of arc transitioning to fall. Pure white background, flat 2D vector art, --ar 16:9`
*   **Fall (3 frames):** `A 3-frame falling horizontal sprite strip of a young Indian boy pilgrim in a white kurta, Facing RIGHT, descending downward with arms raised slightly, white dhoti blowing upward. Pure white background, flat 2D game art, --ar 16:9`
*   **Stun (2 frames):** `A 2-frame stunned dizzy horizontal sprite strip of a young Indian boy pilgrim, Facing RIGHT, slouched posture, head drooping, hand on forehead. Pure white background, flat 2D game art, --ar 16:9`

#### 2. Facing LEFT (Side View)
*(Note: To maintain the absolute physical layout of the diagonal dupatta, use these prompts directly rather than mirroring the Right-facing assets).*
*   **Idle (4 frames):** `A 4-frame idle animation horizontal sprite strip of a young Indian boy pilgrim in a white kurta and dhoti. Standing still, Facing LEFT, subtle breathing loop. White dupatta draped from left shoulder. Pure white background, flat 2D vector art, clean outlines, --ar 16:9`
*   **Walk (6 frames):** `A 6-frame walking cycle horizontal sprite strip of a young Indian boy pilgrim in a white kurta and dhoti, Facing LEFT, walking left with alternating strides. Pure white background, flat 2D game asset, --ar 16:9`
*   **Run (6 frames):** `A 6-frame running cycle horizontal sprite strip of a young Indian boy pilgrim in a white kurta, Facing LEFT, running left, body leaning forward. Pure white background, flat 2D game asset, --ar 16:9`
*   **Jump (4 frames):** `A 4-frame jumping horizontal sprite strip of a young Indian boy pilgrim, Facing LEFT. Crouching → rising → peaking → falling. Pure white background, flat 2D vector art, --ar 16:9`
*   **Fall (3 frames):** `A 3-frame falling horizontal sprite strip of a young Indian boy pilgrim, Facing LEFT, descending. Pure white background, flat 2D game art, --ar 16:9`
*   **Stun (2 frames):** `A 2-frame stunned dizzy horizontal sprite strip of a young Indian boy pilgrim, Facing LEFT, slouched posture. Pure white background, flat 2D game art, --ar 16:9`

#### 3. Facing UP (Back View - Climbing / Interacting)
*   **Idle (4 frames):** `A 4-frame idle animation horizontal sprite strip of a young Indian boy pilgrim in a white kurta and dhoti, Facing UP (back view, looking away from camera). Subtle breathing loop, back of head and shoulders visible. Pure white background, flat 2D vector art, --ar 16:9`
*   **Walk (6 frames):** `A 6-frame walking cycle horizontal sprite strip of a young Indian boy pilgrim, Facing UP (back view, walking away from camera). White robes moving, back profile. Pure white background, flat 2D game asset, --ar 16:9`
*   **Run (6 frames):** `A 6-frame running cycle horizontal sprite strip of a young Indian boy pilgrim, Facing UP (back view, running away from camera). White robes fluttering, back profile. Pure white background, flat 2D game asset, --ar 16:9`
*   **Jump (4 frames):** `A 4-frame jumping horizontal sprite strip of a young Indian boy pilgrim, Facing UP (back view). Launching, rising, peaking, and falling away from camera. Pure white background, flat 2D vector art, --ar 16:9`
*   **Fall (3 frames):** `A 3-frame falling horizontal sprite strip of a young Indian boy pilgrim, Facing UP (back view). Descending away from camera. Pure white background, flat 2D game art, --ar 16:9`
*   **Stun (2 frames):** `A 2-frame stunned dizzy horizontal sprite strip of a young Indian boy pilgrim, Facing UP (back view). Slouched posture, back of head drooping. Pure white background, flat 2D game art, --ar 16:9`

#### 4. Facing DOWN (Front View - Standing / Landing)
*   **Idle (4 frames):** `A 4-frame idle animation horizontal sprite strip of a young Indian boy pilgrim in a white kurta and dhoti, Facing DOWN (front view, looking at camera). Subtle breathing loop. Pure white background, flat 2D vector art, --ar 16:9`
*   **Walk (6 frames):** `A 6-frame walking cycle horizontal sprite strip of a young Indian boy pilgrim, Facing DOWN (front view, walking towards camera). White robes moving. Pure white background, flat 2D game asset, --ar 16:9`
*   **Run (6 frames):** `A 6-frame running cycle horizontal sprite strip of a young Indian boy pilgrim, Facing DOWN (front view, running towards camera). White robes fluttering. Pure white background, flat 2D game asset, --ar 16:9`
*   **Jump (4 frames):** `A 4-frame jumping horizontal sprite strip of a young Indian boy pilgrim, Facing DOWN (front view). Launching, rising, peaking, and falling towards camera. Pure white background, flat 2D vector art, --ar 16:9`
*   **Fall (3 frames):** `A 3-frame falling horizontal sprite strip of a young Indian boy pilgrim, Facing DOWN (front view). Descending towards camera. Pure white background, flat 2D game art, --ar 16:9`
*   **Stun (2 frames):** `A 2-frame stunned dizzy horizontal sprite strip of a young Indian boy pilgrim, Facing DOWN (front view). Slouched posture, dizzy eyes. Pure white background, flat 2D game art, --ar 16:9`

---

### Part C: Standardized Negative Prompt Block
Always append this block to the end of every prompt to eliminate background artifacts, scale shifts, and blending errors:
> **Negative Prompt:** `floor shadow, ground shadow, ambient occlusion, floor plane, ground line, motion blur, depth of field, blurry, cropped heads, overlapping frames, lighting drift, color drift, gradients, 3D shadows, extra limbs, mutated hands, multiple heads, deformed face, text, signature`

---

### Part D: The Crucial Post-Processing Pipeline
Because AI-generated sprite sheets contain inherent noise, scale drifts, and alignment shifts, you **must** perform these post-processing steps before importing them:

#### 1. Frame Selection and Slicing (Resolving Frame-Count Drift)
Image generators rarely produce the exact frame count requested. 
- Ask for 2 or 3 versions (variations) of the prompt.
- Select the cleanest contiguous subset of frames that match the required counts (e.g. 6 walking frames).
- Slice each selected frame manually into individual PNG files or copy them to a clean grid sheet using an image editor (Photoshop, GIMP, or Aseprite).

#### 2. Anchor/Pivot Alignment (Preventing Feet Bobbing)
AI generators do not place the feet on a consistent baseline.
- Define a **Center-Bottom Pivot Point** at the feet of your character.
- Draw a horizontal guide line in your image editor (e.g., at Y = 120 on a 128x128 canvas).
- Align every single frame so that the bottom of the character's feet touches this line perfectly. If you skip this, the character will jitter up and down in-game.

#### 3. Height Normalization (Resolving Scale Drift)
AI characters will drift in size (shrinking/growing) between frames and direction strips.
- Choose a standard vertical height for the character's body (e.g. 110 pixels high from head to foot).
- Scale each frame individually so that the height of the character's body is normalized across all frames.

#### 4. The Asymmetric Sash (Dupatta) Detail
If you decide to save time by mirroring RIGHT-facing frames to get LEFT-facing frames (instead of generating them separately), the white dupatta sash will appear to switch shoulders (draping from right to left). In platformers, players usually overlook this visual flip, but generating them separately with the prompts above will keep the sash drape physically accurate.

#### 5. Loose Fabric and Dhoti Silhouette Cleanup
Loose clothing tends to morph shape between AI frames. Take a soft brush in your editor to smooth out the edge contours of the white dhoti and dupatta, ensuring the silhouette remains consistent from frame to frame.

#### 6. Final Downscale Pass
Once aligned and cleaned on a larger canvas (like 128x128 or 256x256), resize the entire sheet to the clean game proportions (`PLAYER_WIDTH = 48`, `PLAYER_HEIGHT = 64`) or keep it at a precise multiple (like 2x: `96x128`) and let Pygame scale it down with `pygame.transform.smoothscale` for crisp rendering.


