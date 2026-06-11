using Xunit;

namespace Kintsugi.Snap.Tests;

public class QuatTests
{
    private const float Eps = 1e-5f;

    [Fact]
    public void Identity_Has_W_One()
    {
        var q = Quat.Identity;
        Assert.Equal(0f, q.X);
        Assert.Equal(0f, q.Y);
        Assert.Equal(0f, q.Z);
        Assert.Equal(1f, q.W);
    }

    [Fact]
    public void AxisAngle_Zero_Axis_Returns_Identity()
    {
        var q = Quat.AxisAngle(Vec3.Zero, 90f);
        Assert.Equal(1f, q.W, 5);
    }

    [Fact]
    public void AngleBetween_Identity_Identity_Is_Zero()
    {
        Assert.Equal(0f, Quat.AngleBetween(Quat.Identity, Quat.Identity), 5);
    }

    [Theory]
    [InlineData(0f)]
    [InlineData(1f)]
    [InlineData(5f)]
    [InlineData(45f)]
    [InlineData(90f)]
    [InlineData(179f)]
    public void AngleBetween_Recovers_Axis_Angle_Magnitude(float degrees)
    {
        var a = Quat.Identity;
        var b = Quat.AxisAngle(new Vec3(0f, 1f, 0f), degrees);
        float measured = Quat.AngleBetween(a, b);
        Assert.Equal(degrees, measured, 4);
    }

    [Fact]
    public void AngleBetween_Is_Robust_To_Double_Cover()
    {
        var q = Quat.AxisAngle(new Vec3(0f, 1f, 0f), 30f);
        var qNeg = new Quat(-q.X, -q.Y, -q.Z, -q.W);
        Assert.Equal(0f, Quat.AngleBetween(q, qNeg), 4);
    }

    [Fact]
    public void Multiplication_Is_Hamilton_Convention()
    {
        var rotZ90 = Quat.AxisAngle(new Vec3(0f, 0f, 1f), 90f);
        var rotX90 = Quat.AxisAngle(new Vec3(1f, 0f, 0f), 90f);
        var combined = (rotZ90 * rotX90).Normalised();
        float angleFromIdentity = Quat.AngleBetween(combined, Quat.Identity);
        Assert.True(angleFromIdentity > 0f);
        Assert.True(angleFromIdentity < 180f);
    }

    [Fact]
    public void Conjugate_Inverts_Rotation_For_Unit_Quaternions()
    {
        var q = Quat.AxisAngle(new Vec3(1f, 2f, 3f), 47f);
        var roundTrip = (q * q.Conjugate()).Normalised();
        Assert.Equal(0f, Quat.AngleBetween(roundTrip, Quat.Identity), 4);
    }

    [Fact]
    public void Normalised_Of_Zero_Returns_Identity()
    {
        var q = new Quat(0f, 0f, 0f, 0f).Normalised();
        Assert.Equal(1f, q.W);
    }
}
