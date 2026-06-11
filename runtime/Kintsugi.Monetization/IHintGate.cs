namespace Kintsugi.Monetization;

/// <summary>
/// Where a bonus hint was awarded from. Used by analytics; the gate
/// itself treats both sources identically.
/// </summary>
public enum HintGrantSource
{
    /// <summary>Earned by watching a rewarded interstitial.</summary>
    RewardedAd,

    /// <summary>Purchased via IAP credit pack.</summary>
    Iap,

    /// <summary>Granted by the game directly (e.g. a tutorial freebie).</summary>
    SystemGrant,
}

/// <summary>
/// Tracks how many hints the player may consume on the current puzzle,
/// and decides whether a fresh hint request can be served per design
/// decision D6.
/// </summary>
/// <remarks>
/// <b>Routing:</b> the runtime calls
/// <list type="bullet">
///   <item><see cref="OnPuzzleStarted"/> when a puzzle is loaded — this
///   resets the per-puzzle free allowance.</item>
///   <item><see cref="CanUseHint"/> to gate the hint button.</item>
///   <item><see cref="TryConsumeHint"/> when the player taps the hint
///   button. Returns false (and the runtime then offers a rewarded ad
///   or IAP upsell) if the player is out of hints.</item>
///   <item><see cref="GrantBonusHints"/> when an ad reward or IAP
///   succeeds.</item>
/// </list>
/// Premium (ad-removed) players get uncapped hints per D6.
/// </remarks>
public interface IHintGate
{
    bool CanUseHint();

    bool TryConsumeHint();

    int RemainingHints { get; }

    void GrantBonusHints(int count, HintGrantSource source);

    void OnPuzzleStarted(string puzzleId);
}

/// <summary>
/// Hint gate that meters by per-puzzle free allowance plus carry-over
/// bonus hints. Implements decision D6.
/// </summary>
/// <remarks>
/// <para>
/// Each call to <see cref="OnPuzzleStarted"/> tops the per-puzzle
/// counter up to <c>FreeHintsPerPuzzle</c> (it does not stack across
/// puzzles). Bonus hints from ads or IAP are stored separately and
/// carry over between puzzles until consumed.
/// </para>
/// <para>
/// If the player owns the ad-removal SKU, hints are uncapped:
/// <see cref="CanUseHint"/> always returns true,
/// <see cref="RemainingHints"/> reports <see cref="int.MaxValue"/>, and
/// <see cref="TryConsumeHint"/> never fails.
/// </para>
/// </remarks>
public sealed class MeteredHintGate : IHintGate
{
    private readonly IEntitlements _entitlements;
    private readonly int _freeHintsPerPuzzle;
    private int _freeRemaining;
    private int _bonusRemaining;

    public MeteredHintGate(IEntitlements entitlements, int freeHintsPerPuzzle = 3)
    {
        if (freeHintsPerPuzzle < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(freeHintsPerPuzzle));
        }
        _entitlements = entitlements ?? throw new ArgumentNullException(nameof(entitlements));
        _freeHintsPerPuzzle = freeHintsPerPuzzle;
        _freeRemaining = freeHintsPerPuzzle;
    }

    public bool CanUseHint() =>
        _entitlements.HasAdRemoval || _freeRemaining + _bonusRemaining > 0;

    public int RemainingHints =>
        _entitlements.HasAdRemoval ? int.MaxValue : _freeRemaining + _bonusRemaining;

    public bool TryConsumeHint()
    {
        if (_entitlements.HasAdRemoval)
        {
            return true;
        }
        if (_freeRemaining > 0)
        {
            _freeRemaining--;
            return true;
        }
        if (_bonusRemaining > 0)
        {
            _bonusRemaining--;
            return true;
        }
        return false;
    }

    public void GrantBonusHints(int count, HintGrantSource source)
    {
        if (count < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(count));
        }
        _bonusRemaining += count;
    }

    public void OnPuzzleStarted(string puzzleId)
    {
        _freeRemaining = _freeHintsPerPuzzle;
    }
}
