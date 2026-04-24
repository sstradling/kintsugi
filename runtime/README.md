# Kintsugi runtime

Engine-agnostic runtime libraries shared between the Unity client and
the test/CI harness.

## Why netstandard2.1

`netstandard2.1` is consumable by Unity's Mono and IL2CPP runtimes, so
the same DLLs that ship in the game also run unmodified in plain
`dotnet test` for fast CI feedback.

## Projects

- `Kintsugi.Snap` — the snap resolver: pure-math, stateless, decides
  whether a held tray piece is close enough to its target to lock in.
  See `Kintsugi.Snap/SnapResolver.cs`.
- `Kintsugi.Snap.Tests` — xUnit tests for the snap resolver. Targets
  `net8.0` so it can run on a stock SDK install without Unity.

## Build & test

```bash
cd runtime
dotnet test
```

## Routing

User actions for the snap subsystem are routed as follows:

1. Touch input on a tray piece → Unity gesture layer lifts the piece
   into the play space, fixing its orientation relative to the camera
   (per design decision D2).
2. Each frame the piece is held, the assembly controller calls
   `SnapResolver.Resolve(heldWorldPose, assemblyWorldPose,
   pieceLocalTarget, tolerances)`.
3. If `SnapResult.Snapped` is true on release, the piece is animated to
   `SnapResult.TargetWorldPose`, reparented under the assembly node,
   and locked.
4. While held but not snapped, `SnapResult.AngleDegrees` and
   `SnapResult.Distance` drive "warm" haptic and audio feedback.

The resolver has no Unity dependency on purpose: this is the load-bearing
math of the game and we want it under cheap, deterministic, headless
tests.
