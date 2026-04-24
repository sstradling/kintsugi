namespace Kintsugi.Snap;

/// <summary>A rigid-body pose: position + orientation.</summary>
public readonly struct Pose
{
    public readonly Vec3 Position;
    public readonly Quat Rotation;

    public Pose(Vec3 position, Quat rotation)
    {
        Position = position;
        Rotation = rotation;
    }

    public static Pose Identity => new(Vec3.Zero, Quat.Identity);
}

/// <summary>
/// The resolver's verdict for a single drag-resolve call.
/// </summary>
public readonly struct SnapResult
{
    /// <summary>True iff both angular and positional tolerances are met.</summary>
    public readonly bool Snapped;

    /// <summary>Angular distance from the target, in degrees (always &gt;= 0).</summary>
    public readonly float AngleDegrees;

    /// <summary>Positional distance from the target, in world units.</summary>
    public readonly float Distance;

    /// <summary>
    /// The pose to lock the piece into when <see cref="Snapped"/> is true.
    /// Equal to the target world pose; exposed so callers don't have to
    /// recompute it.
    /// </summary>
    public readonly Pose TargetWorldPose;

    public SnapResult(
        bool snapped,
        float angleDegrees,
        float distance,
        Pose targetWorldPose)
    {
        Snapped = snapped;
        AngleDegrees = angleDegrees;
        Distance = distance;
        TargetWorldPose = targetWorldPose;
    }
}

/// <summary>
/// Pure-math snap resolver. Takes the world pose of a held tray piece,
/// the world pose of the assembly, and the piece's local target pose
/// inside the assembly, and decides whether the piece should snap.
/// </summary>
/// <remarks>
/// <b>Routing:</b> the runtime calls <see cref="Resolve"/> every frame a
/// piece is being dragged. On <see cref="SnapResult.Snapped"/> the
/// runtime animates the piece from its current pose to
/// <see cref="SnapResult.TargetWorldPose"/>, then reparents it under the
/// assembly node and locks it. While <see cref="SnapResult.Snapped"/> is
/// false the runtime can still use <see cref="SnapResult.AngleDegrees"/>
/// and <see cref="SnapResult.Distance"/> to drive haptic / audio "warm"
/// feedback as the player approaches the snap envelope.
///
/// This class is intentionally engine-agnostic and stateless so it is
/// trivial to unit-test and so the same code path can run inside Unity
/// or in a CI test harness without modification.
/// </remarks>
public static class SnapResolver
{
    /// <summary>
    /// Compose the assembly's world pose with the piece's local target
    /// pose to produce the world pose at which the piece is considered
    /// "snapped." Exposed because the runtime occasionally needs the
    /// target pose without invoking the full resolve (e.g. for "ghost"
    /// hint outlines).
    /// </summary>
    public static Pose TargetWorldPose(Pose assemblyWorldPose, Pose pieceLocalTarget)
    {
        Quat rot = (assemblyWorldPose.Rotation * pieceLocalTarget.Rotation).Normalised();
        Vec3 rotatedLocal = QuatRotateVec(assemblyWorldPose.Rotation, pieceLocalTarget.Position);
        Vec3 pos = assemblyWorldPose.Position + rotatedLocal;
        return new Pose(pos, rot);
    }

    /// <summary>
    /// Resolve a single frame of a drag. Returns the angular and
    /// positional distance from the target and whether they are both
    /// within the supplied tolerances.
    /// </summary>
    public static SnapResult Resolve(
        Pose heldWorldPose,
        Pose assemblyWorldPose,
        Pose pieceLocalTarget,
        SnapTolerances tolerances)
    {
        Pose target = TargetWorldPose(assemblyWorldPose, pieceLocalTarget);
        float angle = Quat.AngleBetween(
            heldWorldPose.Rotation.Normalised(),
            target.Rotation);
        float distance = (heldWorldPose.Position - target.Position).Length();
        bool snapped =
            angle <= tolerances.MaxAngleDegrees &&
            distance <= tolerances.MaxDistance;
        return new SnapResult(snapped, angle, distance, target);
    }

    /// <summary>Rotate a vector by a unit quaternion.</summary>
    private static Vec3 QuatRotateVec(Quat q, Vec3 v)
    {
        float xx = q.X * q.X;
        float yy = q.Y * q.Y;
        float zz = q.Z * q.Z;
        float xy = q.X * q.Y;
        float xz = q.X * q.Z;
        float yz = q.Y * q.Z;
        float wx = q.W * q.X;
        float wy = q.W * q.Y;
        float wz = q.W * q.Z;
        float rx = v.X * (1f - 2f * (yy + zz)) + v.Y * 2f * (xy - wz) + v.Z * 2f * (xz + wy);
        float ry = v.X * 2f * (xy + wz) + v.Y * (1f - 2f * (xx + zz)) + v.Z * 2f * (yz - wx);
        float rz = v.X * 2f * (xz - wy) + v.Y * 2f * (yz + wx) + v.Z * (1f - 2f * (xx + yy));
        return new Vec3(rx, ry, rz);
    }
}
