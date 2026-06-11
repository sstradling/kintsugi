using Xunit;

namespace Kintsugi.Monetization.Tests;

public class FrequencyCappedAdGateTests
{
    private static readonly DateTimeOffset Start =
        new(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);

    private static (FrequencyCappedAdGate Gate, InMemoryEntitlements Ent, FakeClock Clock)
        BuildGate(int freeBefore = 3, int minPuzzles = 2, double minSeconds = 60)
    {
        var ent = new InMemoryEntitlements();
        var clock = new FakeClock(Start);
        var gate = new FrequencyCappedAdGate(
            ent,
            clock,
            freePuzzlesBeforeFirstAd: freeBefore,
            minIntervalBetweenAds: TimeSpan.FromSeconds(minSeconds),
            minPuzzlesBetweenAds: minPuzzles);
        return (gate, ent, clock);
    }

    private static void CompletePuzzles(FrequencyCappedAdGate gate, int n)
    {
        for (int i = 0; i < n; i++)
        {
            gate.NotifyPuzzleCompleted();
        }
    }

    [Fact]
    public void AdRemoval_Suppresses_Always()
    {
        var (gate, ent, _) = BuildGate();
        ent.SetOwned(Sku.AdRemoval, true);
        CompletePuzzles(gate, 50);
        Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(GameMoment.BetweenPuzzles));
    }

    [Fact]
    public void Non_BetweenPuzzles_Moments_Are_Always_Suppressed()
    {
        var (gate, _, _) = BuildGate();
        CompletePuzzles(gate, 50);

        Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(GameMoment.PuzzleStarted));
        Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(GameMoment.PuzzleCompleted));
        Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(GameMoment.FinisherStarted));
        Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(GameMoment.FinisherCompleted));
        Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(GameMoment.AppForegrounded));
    }

    [Fact]
    public void First_Three_Puzzles_Are_Ad_Free()
    {
        var (gate, _, _) = BuildGate();

        Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(GameMoment.BetweenPuzzles));
        CompletePuzzles(gate, 1);
        Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(GameMoment.BetweenPuzzles));
        CompletePuzzles(gate, 1);
        Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(GameMoment.BetweenPuzzles));
        CompletePuzzles(gate, 1);
        Assert.Equal(AdDecision.Show, gate.RequestInterstitial(GameMoment.BetweenPuzzles));
    }

    [Fact]
    public void After_Showing_An_Ad_Time_Throttle_Suppresses()
    {
        var (gate, _, clock) = BuildGate(minSeconds: 60);
        CompletePuzzles(gate, 3);
        Assert.Equal(AdDecision.Show, gate.RequestInterstitial(GameMoment.BetweenPuzzles));
        gate.NotifyShown();

        CompletePuzzles(gate, 5);
        clock.AdvanceSeconds(30);
        Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(GameMoment.BetweenPuzzles));

        clock.AdvanceSeconds(31);
        Assert.Equal(AdDecision.Show, gate.RequestInterstitial(GameMoment.BetweenPuzzles));
    }

    [Fact]
    public void After_Showing_An_Ad_Puzzle_Throttle_Suppresses()
    {
        var (gate, _, clock) = BuildGate(minPuzzles: 2);
        CompletePuzzles(gate, 3);
        Assert.Equal(AdDecision.Show, gate.RequestInterstitial(GameMoment.BetweenPuzzles));
        gate.NotifyShown();
        clock.AdvanceSeconds(3600);

        CompletePuzzles(gate, 1);
        Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(GameMoment.BetweenPuzzles));

        CompletePuzzles(gate, 1);
        Assert.Equal(AdDecision.Show, gate.RequestInterstitial(GameMoment.BetweenPuzzles));
    }

    [Fact]
    public void Reset_Clears_Session_State()
    {
        var (gate, _, _) = BuildGate();
        CompletePuzzles(gate, 5);
        Assert.Equal(AdDecision.Show, gate.RequestInterstitial(GameMoment.BetweenPuzzles));
        gate.NotifyShown();

        gate.ResetForNewSession();
        Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(GameMoment.BetweenPuzzles));
    }

    [Fact]
    public void Suppress_Verdicts_Do_Not_Advance_Throttles()
    {
        var (gate, _, _) = BuildGate();
        for (int i = 0; i < 10; i++)
        {
            gate.RequestInterstitial(GameMoment.BetweenPuzzles);
        }
        CompletePuzzles(gate, 3);
        Assert.Equal(AdDecision.Show, gate.RequestInterstitial(GameMoment.BetweenPuzzles));
    }

    [Fact]
    public void NoOpAdGate_Always_Suppresses()
    {
        var gate = new NoOpAdGate();
        foreach (var moment in Enum.GetValues<GameMoment>())
        {
            Assert.Equal(AdDecision.Suppress, gate.RequestInterstitial(moment));
        }
    }

    [Theory]
    [InlineData(-1, 0)]
    [InlineData(0, -1)]
    public void Constructor_Rejects_Negative_Thresholds(int freeBefore, int minPuzzles)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            new FrequencyCappedAdGate(
                new InMemoryEntitlements(),
                new FakeClock(Start),
                freePuzzlesBeforeFirstAd: freeBefore,
                minPuzzlesBetweenAds: minPuzzles));
    }

    [Fact]
    public void Constructor_Rejects_Null_Dependencies()
    {
        Assert.Throws<ArgumentNullException>(() =>
            new FrequencyCappedAdGate(null!, new FakeClock(Start)));
        Assert.Throws<ArgumentNullException>(() =>
            new FrequencyCappedAdGate(new InMemoryEntitlements(), null!));
    }
}
