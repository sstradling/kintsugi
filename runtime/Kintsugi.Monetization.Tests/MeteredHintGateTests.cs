using Xunit;

namespace Kintsugi.Monetization.Tests;

public class MeteredHintGateTests
{
    [Fact]
    public void Default_Allowance_Is_Three_Per_Puzzle()
    {
        var gate = new MeteredHintGate(new InMemoryEntitlements());
        Assert.Equal(3, gate.RemainingHints);
        Assert.True(gate.CanUseHint());
    }

    [Fact]
    public void Consuming_Free_Hints_Decrements_Remaining()
    {
        var gate = new MeteredHintGate(new InMemoryEntitlements(), freeHintsPerPuzzle: 2);
        Assert.True(gate.TryConsumeHint());
        Assert.Equal(1, gate.RemainingHints);
        Assert.True(gate.TryConsumeHint());
        Assert.Equal(0, gate.RemainingHints);
        Assert.False(gate.CanUseHint());
        Assert.False(gate.TryConsumeHint());
    }

    [Fact]
    public void Bonus_Hints_From_Ad_Augment_Allowance()
    {
        var gate = new MeteredHintGate(new InMemoryEntitlements(), freeHintsPerPuzzle: 1);
        gate.TryConsumeHint();
        Assert.False(gate.CanUseHint());

        gate.GrantBonusHints(2, HintGrantSource.RewardedAd);
        Assert.Equal(2, gate.RemainingHints);
        Assert.True(gate.TryConsumeHint());
        Assert.True(gate.TryConsumeHint());
        Assert.False(gate.TryConsumeHint());
    }

    [Fact]
    public void OnPuzzleStarted_Resets_Free_Allowance_But_Preserves_Bonuses()
    {
        var gate = new MeteredHintGate(new InMemoryEntitlements(), freeHintsPerPuzzle: 2);
        gate.GrantBonusHints(3, HintGrantSource.Iap);
        gate.TryConsumeHint();
        gate.TryConsumeHint();

        gate.OnPuzzleStarted("puzzle_2");

        Assert.Equal(2 + 3, gate.RemainingHints);
    }

    [Fact]
    public void OnPuzzleStarted_Does_Not_Stack_Free_Allowance()
    {
        var gate = new MeteredHintGate(new InMemoryEntitlements(), freeHintsPerPuzzle: 3);
        gate.OnPuzzleStarted("puzzle_1");
        gate.OnPuzzleStarted("puzzle_2");
        gate.OnPuzzleStarted("puzzle_3");
        Assert.Equal(3, gate.RemainingHints);
    }

    [Fact]
    public void AdRemoval_Uncaps_Hints()
    {
        var ent = new InMemoryEntitlements();
        ent.SetOwned(Sku.AdRemoval, true);
        var gate = new MeteredHintGate(ent, freeHintsPerPuzzle: 0);
        Assert.True(gate.CanUseHint());
        Assert.Equal(int.MaxValue, gate.RemainingHints);

        for (int i = 0; i < 100; i++)
        {
            Assert.True(gate.TryConsumeHint());
        }
    }

    [Fact]
    public void AdRemoval_Acquired_Mid_Puzzle_Takes_Effect_Immediately()
    {
        var ent = new InMemoryEntitlements();
        var gate = new MeteredHintGate(ent, freeHintsPerPuzzle: 1);
        gate.TryConsumeHint();
        Assert.False(gate.CanUseHint());

        ent.SetOwned(Sku.AdRemoval, true);
        Assert.True(gate.CanUseHint());
        Assert.True(gate.TryConsumeHint());
    }

    [Fact]
    public void Constructor_Rejects_Negative_Allowance()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            new MeteredHintGate(new InMemoryEntitlements(), freeHintsPerPuzzle: -1));
    }

    [Fact]
    public void GrantBonusHints_Rejects_Negative_Count()
    {
        var gate = new MeteredHintGate(new InMemoryEntitlements());
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            gate.GrantBonusHints(-1, HintGrantSource.Iap));
    }

    [Fact]
    public void Zero_Free_Allowance_Means_Player_Must_Earn_Or_Buy_Hints()
    {
        var gate = new MeteredHintGate(new InMemoryEntitlements(), freeHintsPerPuzzle: 0);
        Assert.False(gate.CanUseHint());
        Assert.False(gate.TryConsumeHint());

        gate.GrantBonusHints(1, HintGrantSource.RewardedAd);
        Assert.True(gate.TryConsumeHint());
        Assert.False(gate.CanUseHint());
    }
}
