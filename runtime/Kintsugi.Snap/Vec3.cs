namespace Kintsugi.Snap;

/// <summary>
/// Minimal 3D vector. The runtime uses Unity's <c>Vector3</c> at the
/// edges, but the snap resolver itself is engine-agnostic so it can be
/// unit-tested with plain <c>dotnet test</c>.
/// </summary>
public readonly struct Vec3
{
    public readonly float X;
    public readonly float Y;
    public readonly float Z;

    public Vec3(float x, float y, float z)
    {
        X = x;
        Y = y;
        Z = z;
    }

    public static Vec3 Zero => new(0f, 0f, 0f);

    public static Vec3 operator -(Vec3 a, Vec3 b) =>
        new(a.X - b.X, a.Y - b.Y, a.Z - b.Z);

    public static Vec3 operator +(Vec3 a, Vec3 b) =>
        new(a.X + b.X, a.Y + b.Y, a.Z + b.Z);

    public float LengthSquared() => X * X + Y * Y + Z * Z;

    public float Length() => MathF.Sqrt(LengthSquared());

    public override string ToString() => $"({X}, {Y}, {Z})";
}
