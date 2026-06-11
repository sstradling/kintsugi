using Xunit;

namespace Kintsugi.Monetization.Tests;

public class InMemoryEntitlementsTests
{
    [Fact]
    public void Defaults_To_Nothing_Owned()
    {
        var e = new InMemoryEntitlements();
        Assert.False(e.HasAdRemoval);
        Assert.False(e.Owns(Sku.AdRemoval));
        Assert.False(e.Owns(Sku.FillerPackGoldPlatinum));
    }

    [Fact]
    public void SetOwned_True_Reflects_In_HasAdRemoval()
    {
        var e = new InMemoryEntitlements();
        e.SetOwned(Sku.AdRemoval, true);
        Assert.True(e.HasAdRemoval);
        Assert.True(e.Owns(Sku.AdRemoval));
    }

    [Fact]
    public void SetOwned_False_Revokes_Ownership()
    {
        var e = new InMemoryEntitlements();
        e.SetOwned(Sku.AdRemoval, true);
        e.SetOwned(Sku.AdRemoval, false);
        Assert.False(e.HasAdRemoval);
    }

    [Fact]
    public void Filler_Pack_Ownership_Is_Independent_Of_AdRemoval()
    {
        var e = new InMemoryEntitlements();
        e.SetOwned(Sku.FillerPackExotic, true);
        Assert.True(e.Owns(Sku.FillerPackExotic));
        Assert.False(e.HasAdRemoval);
    }
}
