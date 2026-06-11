namespace Kintsugi.Monetization;

/// <summary>
/// Abstracts the system clock so frequency-based rules can be tested
/// without sleeping.
/// </summary>
/// <remarks>
/// Production code wires <see cref="SystemClock"/>; tests wire
/// <c>FakeClock</c> from the test assembly.
/// </remarks>
public interface IClock
{
    DateTimeOffset UtcNow { get; }
}

/// <summary>Trivial wall-clock implementation.</summary>
public sealed class SystemClock : IClock
{
    public DateTimeOffset UtcNow => DateTimeOffset.UtcNow;
}
