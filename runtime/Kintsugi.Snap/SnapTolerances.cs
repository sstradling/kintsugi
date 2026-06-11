namespace Kintsugi.Snap;

/// <summary>
/// Tolerances used by <see cref="SnapResolver"/> to decide whether a held
/// piece is close enough to its target to snap.
/// </summary>
/// <remarks>
/// Per design decisions D1 and D2 (see <c>docs/GAME_PLAN.md</c>):
/// <list type="bullet">
///   <item><b>D1.</b> The distance tolerance is a world-space distance,
///   not a screen-space pixel count. Callers compute it from the
///   assembly's bounding-sphere radius — the recommended starting value
///   is <c>BoundingRadius * 0.015</c> (1.5%).</item>
///   <item><b>D2.</b> Tray pieces do not rotate; the player rotates the
///   assembly to align it with the held piece. The resolver's input
///   poses are therefore in world space, and the target world pose is
///   derived from the assembly's current world pose composed with the
///   piece's local target pose.</item>
/// </list>
/// The default values are the brief's spec ported through D1: 5° angular
/// and 10 distance-units (caller is responsible for scaling).
/// </remarks>
public readonly struct SnapTolerances
{
    /// <summary>Maximum allowed angular distance, in degrees.</summary>
    public readonly float MaxAngleDegrees;

    /// <summary>Maximum allowed positional distance, in world units.</summary>
    public readonly float MaxDistance;

    public SnapTolerances(float maxAngleDegrees, float maxDistance)
    {
        if (maxAngleDegrees < 0f)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maxAngleDegrees),
                "angular tolerance must be non-negative");
        }
        if (maxDistance < 0f)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maxDistance),
                "distance tolerance must be non-negative");
        }
        MaxAngleDegrees = maxAngleDegrees;
        MaxDistance = maxDistance;
    }

    /// <summary>Per-spec defaults: 5° and 10 units.</summary>
    public static SnapTolerances Default => new(5f, 10f);

    /// <summary>
    /// Build tolerances scaled to an assembly bounding radius using the
    /// recommended D1 ratio (1.5% of the bounding radius).
    /// </summary>
    public static SnapTolerances FromBoundingRadius(
        float boundingRadius,
        float ratio = 0.015f,
        float angleDegrees = 5f)
    {
        if (boundingRadius <= 0f)
        {
            throw new ArgumentOutOfRangeException(
                nameof(boundingRadius),
                "bounding radius must be positive");
        }
        return new SnapTolerances(angleDegrees, boundingRadius * ratio);
    }
}
