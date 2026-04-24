namespace Kintsugi.Snap;

/// <summary>
/// Unit quaternion stored as (X, Y, Z, W). Conventions:
/// <list type="bullet">
///   <item>Right-handed coordinate system, matching Unity.</item>
///   <item>Multiplication uses the Hamilton convention: <c>a * b</c> applies
///   <c>b</c> first, then <c>a</c>.</item>
///   <item>Quaternions are <i>not</i> normalised by the constructor — call
///   <see cref="Normalised"/> explicitly when input may be non-unit.</item>
/// </list>
/// </summary>
public readonly struct Quat
{
    public readonly float X;
    public readonly float Y;
    public readonly float Z;
    public readonly float W;

    public Quat(float x, float y, float z, float w)
    {
        X = x;
        Y = y;
        Z = z;
        W = w;
    }

    public static Quat Identity => new(0f, 0f, 0f, 1f);

    /// <summary>
    /// Construct a quaternion that rotates <paramref name="degrees"/> around
    /// an axis. The axis is normalised; if it is zero-length the identity
    /// quaternion is returned.
    /// </summary>
    public static Quat AxisAngle(Vec3 axis, float degrees)
    {
        float lenSq = axis.LengthSquared();
        if (lenSq < 1e-12f)
        {
            return Identity;
        }
        float len = MathF.Sqrt(lenSq);
        float radHalf = degrees * MathF.PI / 360f;
        float s = MathF.Sin(radHalf) / len;
        return new Quat(axis.X * s, axis.Y * s, axis.Z * s, MathF.Cos(radHalf)).Normalised();
    }

    /// <summary>
    /// Hamilton-convention quaternion product. <c>(a * b)</c> applied to a
    /// vector first applies <c>b</c>, then <c>a</c>.
    /// </summary>
    public static Quat operator *(Quat a, Quat b) => new(
        a.W * b.X + a.X * b.W + a.Y * b.Z - a.Z * b.Y,
        a.W * b.Y - a.X * b.Z + a.Y * b.W + a.Z * b.X,
        a.W * b.Z + a.X * b.Y - a.Y * b.X + a.Z * b.W,
        a.W * b.W - a.X * b.X - a.Y * b.Y - a.Z * b.Z);

    public Quat Conjugate() => new(-X, -Y, -Z, W);

    public Quat Normalised()
    {
        float n = MathF.Sqrt(X * X + Y * Y + Z * Z + W * W);
        if (n < 1e-12f)
        {
            return Identity;
        }
        return new Quat(X / n, Y / n, Z / n, W / n);
    }

    /// <summary>
    /// Geodesic angular distance between two unit quaternions, in degrees.
    /// Always returned in the range [0, 180]. Robust to the double-cover
    /// (q and -q represent the same orientation).
    /// </summary>
    /// <remarks>
    /// Uses the <c>2*atan2(|imag(d)|, |real(d)|)</c> form rather than the
    /// more familiar <c>2*acos(|dot|)</c>: <c>acos</c> loses several bits of
    /// precision near 1, which matters here because we routinely compare
    /// against a 5° tolerance.
    /// </remarks>
    public static float AngleBetween(Quat a, Quat b)
    {
        Quat d = a.Conjugate() * b;
        float imagLen = MathF.Sqrt(d.X * d.X + d.Y * d.Y + d.Z * d.Z);
        float realAbs = MathF.Abs(d.W);
        return 2f * MathF.Atan2(imagLen, realAbs) * 180f / MathF.PI;
    }

    public override string ToString() => $"({X}, {Y}, {Z}, {W})";
}
