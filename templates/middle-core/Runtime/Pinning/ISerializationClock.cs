namespace MiddleCore.Runtime.Pinning;

/// <summary>
/// Provides the current serialization timestamp used when a <see cref="ProvenanceStamp"/>
/// is created for a pinning operation.
///
/// Abstracting the clock makes serialization timestamps testable and deterministic.
/// </summary>
public interface ISerializationClock
{
    /// <summary>
    /// Returns the current UTC timestamp as an ISO-8601 string
    /// (format: <c>yyyy-MM-ddTHH:mm:ss.fffffffZ</c>).
    /// </summary>
    string UtcNow();
}

/// <summary>
/// Production implementation of <see cref="ISerializationClock"/> backed by
/// <see cref="DateTimeOffset.UtcNow"/>.
/// </summary>
public sealed class SystemSerializationClock : ISerializationClock
{
    /// <inheritdoc />
    public string UtcNow() =>
        DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffffffZ", System.Globalization.CultureInfo.InvariantCulture);
}
