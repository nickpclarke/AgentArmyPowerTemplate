using Xunit;
using MiddleCore.Runtime.Pinning;

namespace MiddleCore.Tests.Pinning;

/// <summary>
/// Tests for <see cref="ISerializationClock"/> and <see cref="SystemSerializationClock"/>.
/// A fake clock implementation used by other test classes is also validated here.
/// </summary>
public sealed class SerializationClockTests
{
    // -----------------------------------------------------------------------
    // SystemSerializationClock — produces a parseable UTC timestamp
    // -----------------------------------------------------------------------

    [Fact]
    public void SystemClock_UtcNow_ReturnsParseableIso8601UtcString()
    {
        var clock = new SystemSerializationClock();
        string timestamp = clock.UtcNow();

        bool parsed = DateTimeOffset.TryParse(
            timestamp,
            System.Globalization.CultureInfo.InvariantCulture,
            System.Globalization.DateTimeStyles.RoundtripKind,
            out DateTimeOffset dto);

        Assert.True(parsed, $"Timestamp '{timestamp}' could not be parsed as DateTimeOffset.");
        Assert.Equal(TimeSpan.Zero, dto.Offset); // Must be UTC.
    }

    [Fact]
    public void SystemClock_UtcNow_ReturnsNonEmptyString()
    {
        var clock = new SystemSerializationClock();
        string timestamp = clock.UtcNow();

        Assert.False(string.IsNullOrWhiteSpace(timestamp));
    }

    [Fact]
    public void SystemClock_UtcNow_MonotonicallyIncreases()
    {
        var clock = new SystemSerializationClock();
        string t1 = clock.UtcNow();

        // Small busy wait to guarantee clock advances on any platform.
        System.Threading.Thread.Sleep(10);
        string t2 = clock.UtcNow();

        DateTimeOffset dto1 = DateTimeOffset.Parse(t1, System.Globalization.CultureInfo.InvariantCulture);
        DateTimeOffset dto2 = DateTimeOffset.Parse(t2, System.Globalization.CultureInfo.InvariantCulture);

        Assert.True(dto2 >= dto1, $"Clock went backward: {t1} → {t2}");
    }

    // -----------------------------------------------------------------------
    // FakeSerializationClock — used in other tests; validate it here
    // -----------------------------------------------------------------------

    [Fact]
    public void FakeClock_ReturnsPinnedTimestamp()
    {
        const string pinned = "2026-01-15T10:30:00.0000000Z";
        var clock = new FakeSerializationClock(pinned);

        Assert.Equal(pinned, clock.UtcNow());
        Assert.Equal(pinned, clock.UtcNow()); // Idempotent.
    }
}

/// <summary>
/// Test double for <see cref="ISerializationClock"/> that always returns a fixed timestamp.
/// Accessible within the test assembly so all pinning tests can share it.
/// </summary>
internal sealed class FakeSerializationClock(string fixedTimestamp) : ISerializationClock
{
    public string UtcNow() => fixedTimestamp;
}
