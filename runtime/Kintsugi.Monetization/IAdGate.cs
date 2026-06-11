namespace Kintsugi.Monetization;

/// <summary>
/// Points in the game session where the monetization layer may be
/// consulted. Used by <see cref="IAdGate.RequestInterstitial"/> so the
/// gate can enforce "never mid-puzzle, never during finisher" without
/// callers having to interpret rules themselves.
/// </summary>
public enum GameMoment
{
    /// <summary>The brief screen between completing one puzzle and starting the next.</summary>
    BetweenPuzzles,

    /// <summary>The player has just begun assembling a new puzzle.</summary>
    PuzzleStarted,

    /// <summary>The player has just snapped the final piece (before the finisher plays).</summary>
    PuzzleCompleted,

    /// <summary>The finisher animation is about to play.</summary>
    FinisherStarted,

    /// <summary>The finisher animation has just finished.</summary>
    FinisherCompleted,

    /// <summary>The app has returned to the foreground from background.</summary>
    AppForegrounded,
}

/// <summary>The gate's verdict on a single interstitial request.</summary>
public enum AdDecision
{
    /// <summary>The caller should show an interstitial right now.</summary>
    Show,

    /// <summary>The caller should not show an interstitial.</summary>
    Suppress,
}

/// <summary>
/// Decides when an interstitial ad may be shown. Implementations enforce
/// the rules from design decision D4.
/// </summary>
/// <remarks>
/// <b>Routing:</b> the runtime calls
/// <see cref="RequestInterstitial"/> at every <see cref="GameMoment"/>.
/// On <see cref="AdDecision.Show"/> it invokes the ad mediator and then
/// calls <see cref="NotifyShown"/>; on dismissal it calls
/// <see cref="NotifyDismissed"/>. The gate is the single source of
/// truth for ad cadence so the mediator can be swapped without
/// re-deriving the rules.
/// </remarks>
public interface IAdGate
{
    /// <summary>Decide whether an interstitial should be shown at this moment.</summary>
    AdDecision RequestInterstitial(GameMoment moment);

    /// <summary>Record that an interstitial was successfully shown.</summary>
    void NotifyShown();

    /// <summary>Record that the most recently shown interstitial was dismissed.</summary>
    void NotifyDismissed();

    /// <summary>Reset session-scoped counters. Call on session start.</summary>
    void ResetForNewSession();
}

/// <summary>
/// Ad gate used by premium (ad-removed) players and by pre-launch
/// builds: never shows an interstitial.
/// </summary>
public sealed class NoOpAdGate : IAdGate
{
    public AdDecision RequestInterstitial(GameMoment moment) => AdDecision.Suppress;

    public void NotifyShown() { }

    public void NotifyDismissed() { }

    public void ResetForNewSession() { }
}
