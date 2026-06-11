namespace Kintsugi.Monetization;

/// <summary>
/// Frequency-capped ad gate implementing the cadence rules from
/// design decision D4.
/// </summary>
/// <remarks>
/// Rules, in evaluation order — the first matching rule wins:
/// <list type="number">
///   <item>If the player owns the ad-removal SKU → Suppress.</item>
///   <item>If the moment is not <see cref="GameMoment.BetweenPuzzles"/> →
///   Suppress. (Enforces "never mid-puzzle, never on the finisher
///   animation.")</item>
///   <item>If fewer than <c>FreePuzzlesBeforeFirstAd</c> puzzles have
///   been completed this session → Suppress. (The free tier must stay
///   pleasant on first contact.)</item>
///   <item>If less than <c>MinIntervalBetweenAds</c> has elapsed since
///   the last ad → Suppress. (No back-to-back interstitials.)</item>
///   <item>If fewer than <c>MinPuzzlesBetweenAds</c> puzzles have been
///   completed since the last ad → Suppress. (No two ads in three
///   puzzles.)</item>
///   <item>Otherwise → Show.</item>
/// </list>
/// All thresholds are constructor parameters so they can be driven by
/// remote config without a code change.
/// </remarks>
public sealed class FrequencyCappedAdGate : IAdGate
{
    private readonly IEntitlements _entitlements;
    private readonly IClock _clock;
    private readonly int _freePuzzlesBeforeFirstAd;
    private readonly TimeSpan _minIntervalBetweenAds;
    private readonly int _minPuzzlesBetweenAds;

    private int _puzzlesCompletedThisSession;
    private int _puzzlesSinceLastAd;
    private DateTimeOffset? _lastAdShownAt;

    /// <summary>
    /// Build a gate with the cadence rules from D4. Defaults are the
    /// values in the plan — adjust via remote config in production.
    /// </summary>
    /// <param name="entitlements">Source of truth for the ad-removal SKU.</param>
    /// <param name="clock">Wall clock; tests inject a fake.</param>
    /// <param name="freePuzzlesBeforeFirstAd">
    /// Number of puzzles the player completes before the first ad of a
    /// session can appear. Default 3.
    /// </param>
    /// <param name="minIntervalBetweenAds">
    /// Minimum time between two ads. Default 60s.
    /// </param>
    /// <param name="minPuzzlesBetweenAds">
    /// Minimum number of puzzles completed between two ads. Default 2
    /// (i.e. at most one ad per 2–3 puzzles).
    /// </param>
    public FrequencyCappedAdGate(
        IEntitlements entitlements,
        IClock clock,
        int freePuzzlesBeforeFirstAd = 3,
        TimeSpan? minIntervalBetweenAds = null,
        int minPuzzlesBetweenAds = 2)
    {
        if (freePuzzlesBeforeFirstAd < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(freePuzzlesBeforeFirstAd));
        }
        if (minPuzzlesBetweenAds < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(minPuzzlesBetweenAds));
        }
        _entitlements = entitlements ?? throw new ArgumentNullException(nameof(entitlements));
        _clock = clock ?? throw new ArgumentNullException(nameof(clock));
        _freePuzzlesBeforeFirstAd = freePuzzlesBeforeFirstAd;
        _minIntervalBetweenAds = minIntervalBetweenAds ?? TimeSpan.FromSeconds(60);
        _minPuzzlesBetweenAds = minPuzzlesBetweenAds;
    }

    /// <summary>
    /// Notify the gate that a puzzle has been completed. Must be called
    /// before <see cref="RequestInterstitial"/> at
    /// <see cref="GameMoment.BetweenPuzzles"/>.
    /// </summary>
    public void NotifyPuzzleCompleted()
    {
        _puzzlesCompletedThisSession++;
        _puzzlesSinceLastAd++;
    }

    public AdDecision RequestInterstitial(GameMoment moment)
    {
        if (_entitlements.HasAdRemoval)
        {
            return AdDecision.Suppress;
        }
        if (moment != GameMoment.BetweenPuzzles)
        {
            return AdDecision.Suppress;
        }
        if (_puzzlesCompletedThisSession < _freePuzzlesBeforeFirstAd)
        {
            return AdDecision.Suppress;
        }
        if (_lastAdShownAt.HasValue &&
            _clock.UtcNow - _lastAdShownAt.Value < _minIntervalBetweenAds)
        {
            return AdDecision.Suppress;
        }
        if (_lastAdShownAt.HasValue && _puzzlesSinceLastAd < _minPuzzlesBetweenAds)
        {
            return AdDecision.Suppress;
        }
        return AdDecision.Show;
    }

    public void NotifyShown()
    {
        _lastAdShownAt = _clock.UtcNow;
        _puzzlesSinceLastAd = 0;
    }

    public void NotifyDismissed()
    {
    }

    public void ResetForNewSession()
    {
        _puzzlesCompletedThisSession = 0;
        _puzzlesSinceLastAd = 0;
        _lastAdShownAt = null;
    }
}
