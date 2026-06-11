using Xunit;

namespace Kintsugi.Snap.Tests;

public class SnapResolverTests
{
    private static readonly SnapTolerances DefaultTol = new(5f, 10f);

    [Fact]
    public void Snaps_When_Held_Pose_Equals_Target_With_Identity_Assembly()
    {
        var local = new Pose(new Vec3(1f, 2f, 3f), Quat.Identity);
        var assembly = Pose.Identity;
        var result = SnapResolver.Resolve(
            heldWorldPose: new Pose(new Vec3(1f, 2f, 3f), Quat.Identity),
            assemblyWorldPose: assembly,
            pieceLocalTarget: local,
            tolerances: DefaultTol);

        Assert.True(result.Snapped);
        Assert.Equal(0f, result.Distance, 4);
        Assert.Equal(0f, result.AngleDegrees, 4);
    }

    [Fact]
    public void Does_Not_Snap_When_Distance_Exceeds_Tolerance()
    {
        var local = new Pose(new Vec3(0f, 0f, 0f), Quat.Identity);
        var held = new Pose(new Vec3(11f, 0f, 0f), Quat.Identity);
        var result = SnapResolver.Resolve(held, Pose.Identity, local, DefaultTol);
        Assert.False(result.Snapped);
        Assert.Equal(11f, result.Distance, 4);
    }

    [Fact]
    public void Does_Not_Snap_When_Angle_Exceeds_Tolerance()
    {
        var local = new Pose(Vec3.Zero, Quat.Identity);
        var held = new Pose(Vec3.Zero, Quat.AxisAngle(new Vec3(0f, 1f, 0f), 6f));
        var result = SnapResolver.Resolve(held, Pose.Identity, local, DefaultTol);
        Assert.False(result.Snapped);
        Assert.Equal(6f, result.AngleDegrees, 3);
    }

    [Fact]
    public void Snaps_At_Exact_Tolerance_Boundary()
    {
        var local = new Pose(new Vec3(10f, 0f, 0f), Quat.Identity);
        var heldRot = Quat.AxisAngle(new Vec3(0f, 1f, 0f), 5f);
        var held = new Pose(new Vec3(10f, 0f, 0f), heldRot);
        var result = SnapResolver.Resolve(held, Pose.Identity, local, DefaultTol);
        Assert.True(result.Snapped);
    }

    [Fact]
    public void Target_World_Pose_Composes_Assembly_Rotation_With_Local_Position()
    {
        var assemblyRot = Quat.AxisAngle(new Vec3(0f, 1f, 0f), 90f);
        var assembly = new Pose(new Vec3(5f, 0f, 0f), assemblyRot);
        var local = new Pose(new Vec3(1f, 0f, 0f), Quat.Identity);

        var target = SnapResolver.TargetWorldPose(assembly, local);

        Assert.Equal(5f, target.Position.X, 3);
        Assert.Equal(0f, target.Position.Y, 3);
        Assert.Equal(-1f, target.Position.Z, 3);
    }

    [Fact]
    public void Snap_Decision_Is_Computed_In_Assembly_Rotated_Frame()
    {
        var assembly = new Pose(Vec3.Zero, Quat.AxisAngle(new Vec3(0f, 1f, 0f), 90f));
        var local = new Pose(new Vec3(1f, 0f, 0f), Quat.Identity);

        var heldAtRotatedTarget = new Pose(
            new Vec3(0f, 0f, -1f),
            Quat.AxisAngle(new Vec3(0f, 1f, 0f), 90f));
        var rotatedResult = SnapResolver.Resolve(
            heldAtRotatedTarget, assembly, local, DefaultTol);
        Assert.True(rotatedResult.Snapped);

        var heldAtUnrotatedTarget = new Pose(new Vec3(1f, 0f, 0f), Quat.Identity);
        var wrongResult = SnapResolver.Resolve(
            heldAtUnrotatedTarget, assembly, local, DefaultTol);
        Assert.False(wrongResult.Snapped);
    }

    [Fact]
    public void Distance_Scales_With_Bounding_Radius_Per_D1()
    {
        var assembly = new Pose(Vec3.Zero, Quat.Identity);
        var local = new Pose(Vec3.Zero, Quat.Identity);
        var held = new Pose(new Vec3(0.020f, 0f, 0f), Quat.Identity);

        var smallTol = SnapTolerances.FromBoundingRadius(1f);
        var bigTol = SnapTolerances.FromBoundingRadius(2f);

        Assert.False(SnapResolver.Resolve(held, assembly, local, smallTol).Snapped);
        Assert.True(SnapResolver.Resolve(held, assembly, local, bigTol).Snapped);
    }

    [Fact]
    public void Result_Always_Reports_Target_World_Pose_Even_When_Not_Snapped()
    {
        var assembly = new Pose(new Vec3(2f, 3f, 4f), Quat.Identity);
        var local = new Pose(new Vec3(1f, 0f, 0f), Quat.Identity);
        var held = new Pose(new Vec3(99f, 99f, 99f), Quat.Identity);

        var result = SnapResolver.Resolve(held, assembly, local, DefaultTol);

        Assert.False(result.Snapped);
        Assert.Equal(3f, result.TargetWorldPose.Position.X, 4);
        Assert.Equal(3f, result.TargetWorldPose.Position.Y, 4);
        Assert.Equal(4f, result.TargetWorldPose.Position.Z, 4);
    }
}
