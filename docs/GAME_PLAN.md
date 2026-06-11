# Kintsugi — Game Plan

> Working title: **Kintsugi** (the repo name is apt — the Japanese craft of mending broken
> pottery with gold is exactly the spec's "bind pieces with fillers" beat).
> A zen 3D shatter-and-mend puzzle for iOS and Android.

This document is a planning artifact only. It is intentionally exhaustive so that
follow-on work can be split into focused issues / PRs. It does **not** prescribe
implementation yet — open questions and tradeoffs are called out so a human can
make decisions before code is written.

---

## 1. One-paragraph pitch

The player is given a fragment of a 3D object — a vase, a skull, a meteor, a
ship in a bottle — and a tray of remaining shards. They rotate the assembly
freely with touch, drag shards toward it, and shards click into place when
they're close to the right position and orientation. There are no timers, no
fail states, no scores. Once the object is whole, the player picks a binding
material — gold, platinum, lava, wood, bioluminescent gel, rainbow glitter,
sunlight, moss — that flows into the seams and finishes the piece. The
finished piece can be admired, photographed, and added to a personal shelf.

---

## 2. Reference games (the "is this novel?" question)

The conceit is **not** novel; the closest precedents are:

| Game | Platform | How it overlaps | How Kintsugi differs |
|---|---|---|---|
| **Puzzling Places** (Realities.io, 2022) | Quest / PSVR | The defining title of "3D zen jigsaw." Photogrammetry models shattered into ~25–400 pieces, rotate in space, snap when close, no timers. | VR-only; no binding/finishing layer; pieces are scanned real places, not stylized objects. |
| **Assemble With Care** (ustwo, 2019) | iOS / Apple Arcade / Steam | Zen tone, narrative wrapper around 3D object disassembly/reassembly (cassette player, camera, etc.). Touch-first. | Mechanic is "take apart in order, then put back," not free-form spatial assembly. No fillers. |
| **The Room** series (Fireproof, 2012–) | iOS / Android / Steam | Touch-controlled 3D object manipulation, tactile. | Escape-room/lock-puzzle idiom, not jigsaw. |
| **LEGO Builder's Journey** | Switch / Steam / mobile | Zen, minimalist 3D assembly with snap. | Brick grid, not arbitrary shatter. |
| **Tangram-style 3D apps** (Cubic Tangram, 3D Puzzle, Block Puzzle 3D) | Mobile | 3D piece-fitting on phone, snap mechanic. | Geometric primitives, no narrative/finishing layer. |
| **Photogrammetry jigsaw apps** (e.g. *3D Jigsaw Puzzles*, *Tripp*) | Mobile | Direct competitors in the casual store. | Generally low production value; no binding step. |
| **Gorogoa**, **I Love Hue**, **Monument Valley**, **Alto's Odyssey** | Mobile | Same "zen, no-fail" tonal lane Kintsugi sits in. | Different mechanics. |

**Implication:** The base mechanic is well-trodden, especially in VR. The
**differentiators** to lean into are:

1. **The kintsugi finishing step.** No mobile game in this lane treats the
   *seams between pieces* as the hero asset. This is the brand.
2. **Stylized, hand-curated objects** rather than photogrammetry — easier to
   author, ship smaller, and theme into collections (alchemy, oceanic, cosmic…).
3. **Touch-native** rather than VR-port ergonomics.
4. **Collectible "shelf"** of finished pieces with chosen fillers — players
   end up with a personal museum, encouraging replay with different fillers.

---

## 3. Functional requirements (from the brief, expanded)

### 3.1 Core gameplay loop
- **Starter piece**: a non-movable "anchor" fragment of the assembly. Acts as
  the world-space reference frame everything else snaps to.
- **Tray**: a horizontal/curved rail of remaining pieces, scrollable, each
  rendered in 3D with a slow idle rotation so the player can read its shape.
- **Assembly manipulation**:
  - One-finger drag → orbit the assembly on yaw + pitch.
  - Two-finger twist → roll on the camera-Z axis.
  - Two-finger pinch → zoom (camera dolly), within clamped bounds.
  - Inertial damping so it feels like a museum object on a turntable.
- **Tray piece manipulation**:
  - Press & drag a tray piece to lift it into the play space.
  - Piece's orientation is **fixed relative to the camera** while held (per
    spec: tray pieces cannot be rotated/transformed by the player).
  - Release while inside the snap envelope → snap + lock.
  - Release outside → piece returns to the tray with a soft animation.
- **Snap envelope** (per spec):
  - ≤ 5° angular distance from the correct orientation in the assembly's
    local frame.
  - ≤ 10 px from the correct position. **(Open question: screen-space px or
    world-space mm? See §6.)**
  - On snap, piece is reparented to the assembly node and becomes part of
    the rotation group.
- **Completion**: when all pieces are locked, the assembly enters **Finish
  Mode**: filler selection UI appears, player picks one, finisher animation
  plays, finished piece is saved to the shelf.

### 3.2 Non-goals (zen tenet)
- No timer, score, star rating, life/heart system, **ad interstitial during
  play** (per D4 ads are between-puzzle only), no ads on the finisher
  animation, no "wrong piece" fail flash.
- No leaderboards. (Possibly opt-in shelf sharing — see §6.)

### 3.3 Meta layer
- **Shelf**: a 3D room with shelves; finished pieces sit on them. Tap to
  inspect/rotate.
- **Catalog**: list of available puzzles, grouped into themed packs.
- **Filler library**: each filler unlocks via play (e.g. completing N
  puzzles unlocks moss; some are premium). Open question — see §6.
- **Photo mode**: simple camera + lighting presets for the finished piece.

---

## 4. Non-functional requirements

| Area | Target |
|---|---|
| Platforms | iOS 15+, Android 10+ (API 29+). |
| Devices | iPhone 11 / Pixel 4a class as floor; iPad/tablet first-class. |
| Frame rate | 60 fps on floor devices during play; 30 fps acceptable on Finish-Mode shaders if needed. |
| Memory | < 600 MB peak on floor devices; per-puzzle asset budget < 30 MB. |
| Cold-launch | < 4 s on floor devices. |
| Install size | < 200 MB base; puzzles delivered via on-demand resources / Play Asset Delivery. |
| Offline | Fully playable offline after first launch. |
| Accessibility | Color-blind safe filler swatches; reduced-motion mode (kills idle rotation, slows orbit damping); single-finger fallback for two-finger gestures; haptic toggle. |
| Localization | English at launch; string table ready for ~10 locales. |
| Privacy | No PII required to play. Anonymous analytics only with explicit consent. |

---

## 5. Recommended tech stack (with tradeoffs)

### 5.1 Engine
**Recommendation: Unity 2022 LTS + URP.**

- **Unity (URP)** — Mature mobile pipeline, strong shader graph for filler
  materials, asset store ecosystem (DOTween, RayFire), single C# codebase,
  good profiling on device. Royalty terms acceptable for a niche premium title.
- **Unreal 5 mobile** — Overkill; Lumen/Nanite irrelevant on phones; larger
  binary; C++/Blueprint friction for a small team.
- **Godot 4** — Free, lightweight, improving 3D, but mobile shader/perf
  story is still less battle-tested for stylized shaders like volumetric
  bioluminescence; smaller talent pool.
- **Native (SceneKit + ARCore/Filament)** — Two codebases, no shared
  authoring, slowest path. Only consider if AR becomes the core USP.
- **Web/Three.js + Capacitor** — Easiest to prototype, but touch gesture
  precision and shader complexity on low-end Android will hurt. Good for a
  *playable web demo*, not the shipping product.

### 5.2 Key middleware / packages
- **Input System** (Unity) for unified touch + (optional) mouse.
- **DOTween Pro** for snap, return, and finisher animations.
- **Cinemachine** for the orbit camera and Finish-Mode photo cam.
- **Addressables** + **Play Asset Delivery** / **On-Demand Resources** for
  per-puzzle asset streaming.
- **TextMeshPro** for crisp UI.
- **Unity Analytics** or **PostHog Mobile** for opt-in funnel telemetry.

### 5.3 Authoring pipeline (the load-bearing piece)
- **Blender 4.x** with **Cell Fracture** add-on (Voronoi shatter) or
  paid tools (RayFire) for richer shatter patterns.
- A custom **Blender → Unity exporter** that, per puzzle, produces:
  - `pieces/*.fbx` (one per shard; clean watertight mesh; collision mesh).
  - `manifest.json` with: starter-piece id, each piece's target
    position/rotation in assembly local space, neighbor-adjacency graph,
    seam loops (vertex chains shared between adjacent shards — needed for
    the kintsugi finisher).
  - `thumb.png` for catalog.
- This pipeline is the **single biggest engineering risk** (see §8); it
  must exist before content can scale.

---

## 6. Open questions (please answer before coding)

1. **Snap tolerance "10 px" — screen pixels or world units?** 10 screen px
   on a 6" phone is ~0.5 mm, which would feel punishing on a small piece
   and trivial on a giant one. Recommendation: **interpret as world-space
   distance scaled to the assembly's bounding-sphere radius** (e.g. 1.5%
   of bounding radius), and tune. Confirm.
2. **Are tray pieces orientation-locked to the camera, the assembly, or
   the world?** The brief says "cannot rotate." Camera-locked is most
   intuitive (the piece visually matches what the player will see when it
   snaps). Confirm.
3. **Subassembly merging?** May the player join two tray pieces to each
   other off the assembly first? Or strictly tray↔assembly? (Affects data
   model significantly.)
4. ~~**Hint / assist mode?**~~ **Decided (D6):** every puzzle gets a
   small, fixed allowance of free hints (e.g. 3 per puzzle, tunable via
   remote config). Additional hints are unlocked by either watching a
   rewarded interstitial or owning the ad-removal IAP (in which case
   hints are uncapped). The pipeline pre-computes a recommended
   placement order for each puzzle's non-starter pieces and bakes it
   into the manifest as `hint_order`; the runtime simply walks this
   list. The algorithm prefers the most-constrained piece next (most
   already-placed neighbours), with lexicographic tie-breaking for
   determinism. The metering layer — counting free hints, gating
   additional hints behind IAP or ad views — lives in the runtime
   `Kintsugi.Monetization` library, not the pipeline.
5. **Piece-count range per puzzle?** 8 / 25 / 50 / 100? Drives shader,
   memory, and snap-tolerance auto-scaling.
6. **Difficulty / progression model.** Themed packs, linear unlock, daily
   piece, all unlocked? Affects monetization and meta UI.
7. **Monetization.** Premium one-shot (e.g. $4.99), free + IAP filler
   packs, free + puzzle-pack IAP, ad-supported? *Recommendation: premium
   + cosmetic filler packs; ads are tonally wrong for a zen title.*
8. **Account & cross-device save.** Local-only, iCloud/Google
   Play Games Saved Games, or a custom backend? (Custom backend is a
   large, optional scope.)
9. **AR mode?** "Place the assembly on your coffee table." Strong demo,
   but expands testing surface to ARKit + ARCore. Cut for v1?
10. **Photo / share mode?** Watermarked render export. Probably yes for
    organic marketing.
11. **Filler unlock cadence.** Are all 8 fillers available from puzzle 1,
    or do exotic ones (sunlight, bioluminescent gel) unlock later?
12. **Audio direction.** Static ambient bed (à la *Monument Valley*), or
    procedural generative (à la *Mini Metro*)? Per-filler sting on
    completion?
13. **Content target for launch.** 10 puzzles? 25? 50? Drives the
    authoring pipeline's required throughput.
14. **Live ops?** Daily/weekly free puzzle, seasonal filler skins?
    (Implies backend.)

---

## 7. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **Shatter authoring is the bottleneck.** Producing visually pleasing, snap-friendly puzzles is craft-heavy. | High | High | Build the Blender→Unity pipeline as a Phase-0 deliverable. Treat shards as hand-tuned, not pure procedural. Budget art time per puzzle. |
| R2 | **3D touch ergonomics.** Orbiting an assembly *and* dragging a piece *and* not fighting the camera is famously hard on a 6" screen. | High | High | Prototype the gesture model in week 1 (see §9). Reserve a clear modal split: drag-on-empty = orbit; drag-on-piece = lift. Use Cinemachine to keep the framing comfortable. |
| R3 | **Snap feel.** 5°/10px is a starting spec; getting the "thunk" of a snap to feel satisfying takes audio + haptics + animation tuning. | Med | High | Audio + haptic budget; soak test with non-team players early. |
| R4 | **Shader cost of fancy fillers** (volumetric sunlight, bioluminescent gel SSS) on low-end Android. | Med | Med | Per-filler quality tiers; bake to baked emission/normal where possible; don't run finisher shaders during interactive play. |
| R5 | **Asset memory** at 100-piece puzzles. | Med | Med | LOD per piece; share materials; stream pieces via Addressables. |
| R6 | **Cross-platform input parity** (iPad Pencil, foldables, large Android tablets, gesture nav vs button nav). | Med | Low | Input System abstraction; device matrix in QA plan. |
| R7 | **IP / content** if we ever ingest user-submitted models. | Low (until UGC ships) | High | Defer UGC to post-launch; original assets only at launch. |
| R8 | **Scope creep** into "Puzzling Places but with a binder." Risk of building everything and shipping nothing. | High | High | Lock v1 scope at end of Phase 0. AR, UGC, daily puzzle, social are post-launch. |
| R9 | **Store policies** around IAP / privacy manifests / age rating. | Low | Med | Standard checklist before submission. |

---

## 8. Dependencies

### 8.1 External services / SDKs
- Apple App Store Connect + Google Play Console accounts.
- **In-app purchase**: Unity IAP + StoreKit 2 / Google Billing v6 (used
  for both the ad-removal SKU and cosmetic filler-pack SKUs per D4).
- **Ad mediation**: AppLovin MAX or Google AdMob — interstitial only,
  never rewarded video for non-hint flows, never banners, between-puzzle
  only. Mediator choice deferred until Phase 4; both are evaluated for
  COPPA / age-rating compliance and EU consent (CMP) support. The ad
  call site is abstracted behind the `IAdGate` interface in
  `Kintsugi.Monetization` (already implemented) so swapping mediators
  is a one-file change.
- **Cloud save** (optional): iCloud Key-Value / Play Games Saved Games.
  The ad-removal entitlement must be restored from the store on
  reinstall rather than read from cloud save (store-of-record is the
  only audit-proof source).
- **Analytics** (opt-in): Unity Analytics or PostHog. Funnel must
  include free-to-ad-removed conversion (the dominant revenue funnel
  under D4); see the telemetry spec referenced in §13.
- **Crash reporting**: Unity Cloud Diagnostics or Sentry.
- **CDN for streamed puzzle packs** (optional, post-launch).

### 8.2 Internal authoring
- 3D modeller(s) for source objects.
- Blender pipeline scripts (Python).
- Sound designer (ambient + per-filler completion stings).
- One-time: branding, logo, store assets, trailer.

### 8.3 Code-time dependencies (rough)
- Unity 2022 LTS (or 2023 LTS once stable).
- DOTween, Cinemachine, Input System, TextMeshPro, Addressables.
- A small math lib for stable quaternion-distance / Voronoi adjacency
  helpers (or roll our own — small surface).

---

## 9. Asset inventory (rough)

### 9.1 3D
- **Source models** (~10–25 for launch): vase, skull, geode, meteor,
  origami crane, miniature ship, lantern, mask, totem, conch, gear,
  crystal, bonsai pot, music box, astrolabe… Pick a coherent collection
  theme per pack.
- **Per puzzle**: shattered shard meshes + collision meshes + manifest.
- **Shelf room** environment.
- **Tray** prop / rail.

### 9.2 Materials & shaders
- Base PBR for objects (ceramic, stone, metal, wood, glass).
- Per-filler "seam" shader variants:
  - **Gold / Platinum** — anisotropic metal, baked AO in seam.
  - **Lava** — emissive scrolling noise, heat-shimmer post.
  - **Wood** — lathe-grain, displacement.
  - **Bioluminescent gel** — translucent SSS, slow pulse emission.
  - **Rainbow glitter** — view-dependent iridescence.
  - **Sunlight** — additive godray cone clipped to seam volume.
  - **Moss** — shell-based instanced grass on the seam strip.

### 9.3 UI
- Catalog grid, tray, filler picker, settings, shelf, photo mode HUD.
- Iconography, font (1 display + 1 body), color tokens.

### 9.4 Audio
- 3–5 ambient beds (loopable).
- Per-piece pickup, hover-near-snap, snap (rich), invalid-release.
- Per-filler completion sting + ambient bed swap.

### 9.5 Haptics
- Light tick on hover-into-envelope; medium thunk on snap; success
  pattern on completion.

---

## 10. High-level architecture (sketch)

```
+-----------------------------+
|           UI Layer          |  Catalog • Tray • FillerPicker • Shelf
+--------------+--------------+
               |
+--------------v--------------+
|       Game State (FSM)      |  Browse → Loading → Playing → Finishing → Saved
+--------------+--------------+
               |
+--------------v--------------+      +--------------------------+
|     Assembly Controller     +<---->+   Puzzle Asset Loader    |
|  - holds Starter root node  |      |  (Addressables / PAD)    |
|  - parents snapped pieces   |      +--------------------------+
|  - exposes orbit transform  |
+------+-----------+----------+
       |           |
+------v---+   +---v---------------+
| Gesture  |   |  Snap Resolver    |  (per-frame: held-piece pose vs target;
|  Router  |   |                   |   if within 5° + Δd → animate-to-snap → lock)
+----------+   +-------------------+
                       |
+----------------------v----------------------+
|         Finisher / Filler Subsystem         |  selects shader stack,
|   - seam-strip mesh per shard adjacency     |  drives finishing animation,
|   - per-filler material + VFX + audio       |  emits "Completed" event.
+---------------------------------------------+
```

Data model essentials:

- `PuzzleManifest { id, sourceModelId, pieces[], starterPieceId, seams[] }`
- `Piece { id, meshRef, targetLocalPos, targetLocalRot, neighbors[] }`
- `Seam { pieceA, pieceB, vertexLoop[] }`  ← used by the finisher to
  generate the strip the filler renders along.

---

## 11. Phased delivery plan

> Phases are scope-ordered, not time-boxed. Each phase ends with a
> demoable milestone and a go/no-go.

### Phase 0 — Foundations & risk-burn-down
- Stand up Unity project, URP, Input System, Addressables.
- **Vertical-slice prototype** of one hand-fractured object (5 pieces,
  no filler, no UI) on a real device. Validates R2 (gesture model).
- Author the Blender → Unity export pipeline end-to-end on one puzzle.
  Validates R1.
- Decide all open questions in §6.

### Phase 1 — Core loop
- Tray UI + scroll.
- Snap resolver with tunable tolerances (5° / world-scaled distance).
- Snap audio + haptic + animation polish.
- Catalog with 3 puzzles (low / mid / high piece count).
- Settings: reduced motion, haptic toggle, audio mix.

### Phase 2 — Finisher
- Seam-strip generator from manifest.
- Two fillers shipped: **gold** (signature) + **moss** (cheap
  shell-grass). Validates the shader-variant architecture.
- Finishing animation + sting.
- Shelf v1 (flat list, tap to inspect).

### Phase 3 — Content & polish
- Remaining 6 fillers, behind quality tiers.
- Launch puzzle catalog (target N — see §6 q13).
- Shelf v2 (3D room).
- Photo mode.
- Accessibility pass.
- Localization pass.

### Phase 4 — Store readiness
- IAP wired per D4: ad-removal SKU + cosmetic filler-pack SKUs (Sku
  constants already defined in `Kintsugi.Monetization`).
- Ad mediator integrated behind the existing `IAdGate` abstraction;
  interstitial cadence (every 2–3 completed puzzles) tunable via remote
  config so we can adjust without a release.
- Hint metering (`IHintGate`) wired to rewarded-ad and IAP-credit
  callbacks per D6.
- Restore-purchases flow tested on both stores.
- CMP / consent flow (GDPR, ATT, Google UMP) wired ahead of ads.
- Privacy manifest, age rating, store listings, trailer.
- Soft launch in 1–2 territories; observe retention and free-to-
  ad-removed conversion.
- Crash + analytics dashboards.

### Post-launch (not v1)
- AR mode.
- Daily / weekly free puzzle.
- UGC ("upload your own model and shatter it").
- Cross-device cloud save.
- Cosmetic seasonal fillers.

---

## 12. Initial issue list (suggested PRs to file)

1. `chore: scaffold Unity project + URP + Input System`
2. `pipeline: Blender Cell-Fracture exporter producing manifest + meshes`
3. `proto: orbit camera + single-piece drag/snap on device`
4. `feat: PuzzleManifest data model + loader`
5. `feat: snap resolver (5° + world-scaled distance), unit-tested`
6. `feat: tray UI with idle rotation + scroll`
7. `feat: assembly controller (orbit + reparent on snap)`
8. `feat: completion detector → Finish Mode FSM transition`
9. `feat: seam-strip mesh generator from manifest`
10. `feat: filler — gold (shader + VFX + audio + haptic)`
11. `feat: filler — moss (shell instancing)`
12. `feat: shelf v1 + finished-piece persistence`
13. `feat: settings (reduced motion, haptic, audio mix, color-blind)`
14. `chore: addressables + on-demand puzzle delivery`
15. `qa: device matrix smoke tests`
16. `chore: privacy manifest + store listing scaffolding`

Each issue should carry an owner, an acceptance test, and link back to the
relevant section of this doc.

---

## 13. Reflection (per project conventions)

**Scalability & maintainability.** The architecture deliberately isolates
the three things most likely to change: (a) the **authoring pipeline**,
which is a Blender-side concern that emits a stable JSON manifest the
runtime never has to know the internals of; (b) the **snap resolver**,
which is a pure function of `(heldPose, targetPose, tolerances)` and is
trivially unit-testable in isolation from rendering; and (c) the
**filler/finisher subsystem**, designed as a registry of shader+VFX+audio
bundles so adding a 9th filler is an asset+config change, not a code
change. The biggest scaling lever is **content throughput**, not code —
once the Blender exporter is solid, puzzles become an art-and-config
workflow rather than an engineering one, which is the right shape for a
small team shipping a catalog.

**Suggested next steps / improvements.** With monetization settled on
free-with-ads + ad-removal IAP + cosmetic filler-pack IAPs (D4) and the
runtime gates already implemented in `Kintsugi.Monetization`, two
follow-ons matter most: (1) a **telemetry spec** for the
free-to-ad-removed conversion funnel — ad-impression counts per
session, puzzles-completed-before-conversion, hint-consumption rate,
filler-pack attach rate — these are the metrics that decide whether the
title is economically viable and they should not be retrofitted; and
(2) a gesture-model prototype on a real device handed to 3–5 non-team
players, because the *feel* of orbit-vs-drag on touch is the dominant
determinant of whether this game is pleasant or frustrating and it is
the one thing this plan cannot validate on paper. The remaining open
questions in §6.3 (progression model, account/cloud-save, AR, photo
mode, filler unlock cadence, audio direction, content target,
live-ops) can be closed in parallel without blocking either of these.
