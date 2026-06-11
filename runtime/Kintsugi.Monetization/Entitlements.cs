namespace Kintsugi.Monetization;

/// <summary>
/// Tracks which IAP SKUs the current player owns.
/// </summary>
/// <remarks>
/// Per decision D4 the ad-removal entitlement is store-of-record: the
/// production implementation must consult StoreKit / Google Billing on
/// app start (not cloud save) and call <c>SetOwned</c> with the
/// authoritative result. The interface itself is stateful but
/// deliberately simple — production wiring sits behind it.
/// </remarks>
public interface IEntitlements
{
    /// <summary>
    /// True iff the player owns the ad-removal IAP. When true,
    /// <see cref="IAdGate"/> always returns <see cref="AdDecision.Suppress"/>
    /// and <see cref="IHintGate"/> treats hints as uncapped.
    /// </summary>
    bool HasAdRemoval { get; }

    /// <summary>True iff the player owns the SKU with the given id.</summary>
    bool Owns(string sku);
}

/// <summary>
/// In-memory entitlements suitable for tests and pre-launch builds.
/// Production builds wire a store-backed implementation.
/// </summary>
public sealed class InMemoryEntitlements : IEntitlements
{
    private readonly HashSet<string> _owned = new();

    public bool HasAdRemoval => _owned.Contains(Sku.AdRemoval);

    public bool Owns(string sku) => _owned.Contains(sku);

    public void SetOwned(string sku, bool owned)
    {
        if (owned)
        {
            _owned.Add(sku);
        }
        else
        {
            _owned.Remove(sku);
        }
    }
}
