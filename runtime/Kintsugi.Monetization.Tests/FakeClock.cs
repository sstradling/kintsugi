namespace Kintsugi.Monetization.Tests;

/// <summary>
/// Test-only clock that advances only when the test moves it forward.
/// </summary>
public sealed class FakeClock : IClock
{
    public FakeClock(DateTimeOffset start)
    {
        UtcNow = start;
    }

    public DateTimeOffset UtcNow { get; private set; }

    public void Advance(TimeSpan delta) => UtcNow += delta;

    public void AdvanceSeconds(double seconds) =>
        Advance(TimeSpan.FromSeconds(seconds));
}
