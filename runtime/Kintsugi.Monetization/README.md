# Kintsugi.Monetization

Engine-agnostic monetization gates that implement design decisions D4
(ads + IAP cadence) and D6 (hint metering) from
`docs/GAME_PLAN.md`. All decisions are pure functions of injected state
so the library is testable with plain `dotnet test`, with no Unity or
store SDK in the loop.

## Components

| Type | Purpose |
|---|---|
| `Sku` | Stable IAP SKU identifiers (must match App Store Connect and Google Play exactly). |
| `IClock` / `SystemClock` | Time abstraction so frequency rules are testable. |
| `IEntitlements` / `InMemoryEntitlements` | Tracks which SKUs the player owns. Production wires this to the store; tests wire in-memory. |
| `IAdGate` | Decides whether an interstitial should be shown right now. |
| `FrequencyCappedAdGate` | The D4 implementation: never mid-puzzle, never on finisher, first 3 puzzles ad-free, min interval 60s, min 2 puzzles between ads. All thresholds are constructor parameters so they can be driven by remote config. |
| `NoOpAdGate` | Always suppresses. Used for ad-removed players and pre-launch builds. |
| `IHintGate` | Decides whether the player may consume a hint right now. |
| `MeteredHintGate` | The D6 implementation: per-puzzle free allowance (default 3), plus carry-over bonus hints earned from rewarded ads or IAP. Premium (ad-removed) players are uncapped. |

## Routing

The runtime wires these gates at startup. On every `GameMoment` the
ad gate decides whether to show an interstitial; on every hint button
tap the hint gate decides whether the hint is free, costs a bonus
credit, or triggers an upsell offer. The ad mediator (AppLovin /
AdMob) lives behind a separate adapter and never embeds any of these
rules itself — this library is the single source of truth.

```
Game event -> IAdGate.RequestInterstitial(moment)
              -> Show:    mediator.ShowInterstitial() -> gate.NotifyShown/Dismissed
              -> Suppress: continue

Hint tap   -> IHintGate.TryConsumeHint()
              -> true:    show hint
              -> false:   offer rewarded-ad or IAP upsell
                          on reward: gate.GrantBonusHints(N, source)
```

## Build & test

```bash
cd runtime
dotnet test
```
