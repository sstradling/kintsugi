using Xunit;

namespace Kintsugi.Snap.Tests;

public class SnapTolerancesTests
{
    [Fact]
    public void Default_Matches_Brief_Spec()
    {
        var t = SnapTolerances.Default;
        Assert.Equal(5f, t.MaxAngleDegrees);
        Assert.Equal(10f, t.MaxDistance);
    }

    [Fact]
    public void FromBoundingRadius_Uses_D1_Ratio()
    {
        var t = SnapTolerances.FromBoundingRadius(2f);
        Assert.Equal(5f, t.MaxAngleDegrees);
        Assert.Equal(0.03f, t.MaxDistance, 5);
    }

    [Fact]
    public void FromBoundingRadius_Allows_Custom_Ratio()
    {
        var t = SnapTolerances.FromBoundingRadius(2f, ratio: 0.05f, angleDegrees: 7f);
        Assert.Equal(7f, t.MaxAngleDegrees);
        Assert.Equal(0.10f, t.MaxDistance, 5);
    }

    [Fact]
    public void Negative_Angle_Throws()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new SnapTolerances(-1f, 1f));
    }

    [Fact]
    public void Negative_Distance_Throws()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new SnapTolerances(1f, -1f));
    }

    [Fact]
    public void FromBoundingRadius_Rejects_Non_Positive_Radius()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => SnapTolerances.FromBoundingRadius(0f));
        Assert.Throws<ArgumentOutOfRangeException>(
            () => SnapTolerances.FromBoundingRadius(-1f));
    }
}
