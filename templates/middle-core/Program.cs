using System.Text.Json;
using System.Text.Json.Serialization;

var builder = WebApplication.CreateBuilder(args);
builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower;
    options.SerializerOptions.Converters.Add(new JsonStringEnumConverter(JsonNamingPolicy.KebabCaseLower));
});
builder.Services.AddSingleton<BusinessObjectCatalogStore>();

var app = builder.Build();

app.MapGet("/", (BusinessObjectCatalogStore store) =>
{
    BusinessObjectCatalog catalog = store.Load();
    return Results.Content(CatalogExplorer.Render(catalog), "text/html; charset=utf-8");
});

app.MapGet("/health", (BusinessObjectCatalogStore store) =>
{
    BusinessObjectCatalog catalog = store.Load();
    return Results.Ok(new MiddleCoreHealth(
        "ok",
        "middle-core",
        catalog.CatalogId,
        catalog.SchemaVersion,
        catalog.ObjectTypes.Count,
        catalog.Scenarios.Count));
});

app.MapGet("/catalog", (BusinessObjectCatalogStore store) => Results.Ok(store.Load()));
app.MapGet("/objects", (BusinessObjectCatalogStore store) => Results.Ok(store.Load().ObjectTypes));
app.MapGet("/scenarios", (BusinessObjectCatalogStore store) => Results.Ok(store.Load().Scenarios));

app.MapGet("/objects/{id}", (string id, BusinessObjectCatalogStore store) =>
{
    BusinessObjectType? item = store.Load().ObjectTypes.FirstOrDefault(candidate => candidate.Id == id);
    return item is null ? Results.NotFound(new ErrorEnvelope("object_not_found", id)) : Results.Ok(item);
});

app.MapGet("/scenarios/{id}", (string id, BusinessObjectCatalogStore store) =>
{
    ScenarioDefinition? item = store.Load().Scenarios.FirstOrDefault(candidate => candidate.Id == id);
    return item is null ? Results.NotFound(new ErrorEnvelope("scenario_not_found", id)) : Results.Ok(item);
});

app.Run();

public sealed class BusinessObjectCatalogStore
{
    private static readonly JsonSerializerOptions Options = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        PropertyNameCaseInsensitive = true,
        Converters = { new JsonStringEnumConverter(JsonNamingPolicy.KebabCaseLower) }
    };

    private readonly Lazy<BusinessObjectCatalog> catalog;

    public BusinessObjectCatalogStore(IConfiguration configuration)
    {
        string catalogPath = configuration["BUSINESS_OBJECT_CATALOG"] ?? "/app/catalog.json";
        catalog = new Lazy<BusinessObjectCatalog>(
            () => LoadFromDisk(catalogPath),
            LazyThreadSafetyMode.ExecutionAndPublication);
    }

    public BusinessObjectCatalog Load() => catalog.Value;

    private static BusinessObjectCatalog LoadFromDisk(string catalogPath)
    {
        string json = File.ReadAllText(catalogPath);
        BusinessObjectCatalog catalog = JsonSerializer.Deserialize<BusinessObjectCatalog>(json, Options)
            ?? throw new InvalidOperationException("Business object catalog could not be deserialized.");

        catalog.Validate();
        return catalog;
    }
}

public sealed record BusinessObjectCatalog(
    string SchemaVersion,
    string CatalogId,
    IReadOnlyList<ServiceLayer> ServiceLayers,
    IReadOnlyList<BusinessObjectType> ObjectTypes,
    IReadOnlyList<ScenarioDefinition> Scenarios)
{
    public void Validate()
    {
        List<string> errors = [];

        if (SchemaVersion != "business-object-catalog.v1")
            errors.Add("Catalog schema_version must be business-object-catalog.v1.");
        if (ServiceLayers.Count == 0) errors.Add("Catalog must define service layers.");
        if (ObjectTypes.Count == 0) errors.Add("Catalog must define object types.");
        if (Scenarios.Count == 0) errors.Add("Catalog must define scenarios.");

        HashSet<string> requiredLayers = new(StringComparer.Ordinal)
        {
            "arcadedb-capability-services",
            "platform-operational-services",
            "meta-services"
        };
        HashSet<string> layerIds = BuildUniqueIdSet(ServiceLayers.Select(layer => layer.Id), "service layer", errors);
        foreach (string layerId in requiredLayers)
        {
            if (!layerIds.Contains(layerId)) errors.Add($"Catalog is missing required service layer '{layerId}'.");
        }

        HashSet<string> objectIds = BuildUniqueIdSet(ObjectTypes.Select(item => item.Id), "object type", errors);
        HashSet<string> scenarioIds = BuildUniqueIdSet(Scenarios.Select(item => item.Id), "scenario", errors);
        HashSet<string> capabilityIds = new(StringComparer.Ordinal);

        foreach (BusinessObjectType item in ObjectTypes)
        {
            RequireNonEmpty(item.DisplayName, $"Object '{item.Id}' display_name", errors);
            RequireNonEmpty(item.Description, $"Object '{item.Id}' description", errors);
            if (!layerIds.Contains(item.OwnedByLayer))
                errors.Add($"Object '{item.Id}' references unknown owned_by_layer '{item.OwnedByLayer}'.");
            if (item.States.Count == 0) errors.Add($"Object '{item.Id}' must define at least one state.");
            if (item.ProviderMappings.Count == 0) errors.Add($"Object '{item.Id}' must define provider mappings.");
            if (item.RedactionPolicy.Count == 0) errors.Add($"Object '{item.Id}' must define a redaction policy.");

            foreach (ProviderMapping mapping in item.ProviderMappings)
            {
                RequireNonEmpty(mapping.Provider, $"Object '{item.Id}' provider", errors);
                if (mapping.Records.Count == 0) errors.Add($"Object '{item.Id}' provider '{mapping.Provider}' must define records.");
                if (mapping.Capabilities.Count == 0) errors.Add($"Object '{item.Id}' provider '{mapping.Provider}' must define capabilities.");
                foreach (string capability in mapping.Capabilities) capabilityIds.Add(capability);
            }

            foreach (ObjectRelationship relationship in item.Relationships)
            {
                if (!objectIds.Contains(relationship.Target))
                    errors.Add($"Object '{item.Id}' relationship '{relationship.Type}' targets unknown object '{relationship.Target}'.");
            }

            foreach (string scenarioId in item.ScenarioMappings)
            {
                if (!scenarioIds.Contains(scenarioId))
                    errors.Add($"Object '{item.Id}' maps to unknown scenario '{scenarioId}'.");
            }
        }

        foreach (ScenarioDefinition scenario in Scenarios)
        {
            RequireNonEmpty(scenario.DisplayName, $"Scenario '{scenario.Id}' display_name", errors);
            RequireNonEmpty(scenario.Description, $"Scenario '{scenario.Id}' description", errors);
            if (scenario.ServiceLayers.Count == 0) errors.Add($"Scenario '{scenario.Id}' must reference at least one service layer.");
            if (scenario.Outputs.Count == 0) errors.Add($"Scenario '{scenario.Id}' must define outputs.");
            if (scenario.Capabilities.Count == 0) errors.Add($"Scenario '{scenario.Id}' must define capabilities.");
            if (scenario.SafetyPolicy.Count == 0) errors.Add($"Scenario '{scenario.Id}' must define a safety policy.");

            foreach (string layerId in scenario.ServiceLayers)
            {
                if (!layerIds.Contains(layerId))
                    errors.Add($"Scenario '{scenario.Id}' references unknown service layer '{layerId}'.");
            }

            foreach (string input in scenario.Inputs)
            {
                if (!objectIds.Contains(input))
                    errors.Add($"Scenario '{scenario.Id}' references unknown input object '{input}'.");
            }

            foreach (string output in scenario.Outputs)
            {
                if (!objectIds.Contains(output))
                    errors.Add($"Scenario '{scenario.Id}' references unknown output object '{output}'.");
            }

            foreach (string capability in scenario.Capabilities)
            {
                if (!capabilityIds.Contains(capability))
                    errors.Add($"Scenario '{scenario.Id}' references unknown capability '{capability}'.");
            }

            if (scenario.McpEligible && (scenario.InputSchema is null || scenario.OutputSchema is null))
            {
                errors.Add($"Scenario '{scenario.Id}' is MCP eligible but is missing input_schema or output_schema.");
            }
        }

        if (errors.Count > 0)
            throw new InvalidOperationException($"Business object catalog validation failed: {string.Join(" ", errors)}");
    }

    private static HashSet<string> BuildUniqueIdSet(IEnumerable<string> values, string label, List<string> errors)
    {
        HashSet<string> seen = new(StringComparer.Ordinal);
        foreach (string value in values)
        {
            if (string.IsNullOrWhiteSpace(value)) errors.Add($"A {label} id is empty.");
            else if (!seen.Add(value)) errors.Add($"Duplicate {label} id '{value}'.");
        }
        return seen;
    }

    private static void RequireNonEmpty(string value, string label, List<string> errors)
    {
        if (string.IsNullOrWhiteSpace(value)) errors.Add($"{label} must be non-empty.");
    }
}

public sealed record ServiceLayer(string Id, string DisplayName, string Purpose);

public sealed record BusinessObjectType(
    string Id,
    string DisplayName,
    string Description,
    string OwnedByLayer,
    IReadOnlyList<string> States,
    IReadOnlyList<ProviderMapping> ProviderMappings,
    IReadOnlyList<ObjectRelationship> Relationships,
    IReadOnlyList<string> ScenarioMappings,
    McpEligibility McpEligibility,
    IReadOnlyList<string> RedactionPolicy);

public sealed record ProviderMapping(
    string Provider,
    IReadOnlyList<string> Records,
    IReadOnlyList<string> Capabilities);

public sealed record ObjectRelationship(string Type, string Target);

public sealed record ScenarioDefinition(
    string Id,
    string DisplayName,
    string Description,
    IReadOnlyList<string> ServiceLayers,
    IReadOnlyList<string> Inputs,
    IReadOnlyList<string> Outputs,
    IReadOnlyList<string> Capabilities,
    IReadOnlyList<string> SafetyPolicy,
    bool McpEligible,
    JsonElement? InputSchema,
    JsonElement? OutputSchema);

public enum McpEligibility
{
    None,
    ReadOnly,
    GuardedMutation
}

public sealed record MiddleCoreHealth(
    string Status,
    string Service,
    string CatalogId,
    string SchemaVersion,
    int ObjectTypes,
    int Scenarios);

public sealed record ErrorEnvelope(string Error, string Id);

public static class CatalogExplorer
{
    public static string Render(BusinessObjectCatalog catalog)
    {
        Dictionary<string, int> objectCountByLayer = catalog.ObjectTypes
            .GroupBy(item => item.OwnedByLayer)
            .ToDictionary(group => group.Key, group => group.Count(), StringComparer.Ordinal);

        Dictionary<string, int> scenarioCountByLayer = catalog.Scenarios
            .SelectMany(scenario => scenario.ServiceLayers)
            .GroupBy(layer => layer)
            .ToDictionary(group => group.Key, group => group.Count(), StringComparer.Ordinal);

        string layerCards = string.Join("", catalog.ServiceLayers.Select(layer =>
            $"""
            <article class="layer-card">
              <div class="kicker">service family</div>
              <h2>{Html(layer.DisplayName)}</h2>
              <p>{Html(layer.Purpose)}</p>
              <div class="metrics">
                <span>{objectCountByLayer.GetValueOrDefault(layer.Id)} objects</span>
                <span>{scenarioCountByLayer.GetValueOrDefault(layer.Id)} scenarios</span>
              </div>
            </article>
            """));

        string objectCards = string.Join("", catalog.ObjectTypes.Select(item =>
            $"""
            <article class="object-card">
              <div class="row">
                <h3>{Html(item.DisplayName)}</h3>
                <span class="pill">{Html(item.McpEligibility.ToString())}</span>
              </div>
              <p>{Html(item.Description)}</p>
              <div class="chips">
                <span>{Html(item.OwnedByLayer)}</span>
                <span>{item.States.Count} states</span>
                <span>{string.Join(", ", item.ProviderMappings.Select(mapping => Html(mapping.Provider)).Distinct())}</span>
              </div>
              <a href="/objects/{Uri.EscapeDataString(item.Id)}">Open object contract</a>
            </article>
            """));

        string scenarioRows = string.Join("", catalog.Scenarios.Select(item =>
            $"""
            <tr>
              <td><a href="/scenarios/{Uri.EscapeDataString(item.Id)}">{Html(item.DisplayName)}</a></td>
              <td>{Html(string.Join(", ", item.ServiceLayers))}</td>
              <td>{item.Capabilities.Count}</td>
              <td>{(item.McpEligible ? "yes" : "no")}</td>
              <td>{Html(string.Join(", ", item.Outputs))}</td>
            </tr>
            """));

        return $$"""
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>middle-core catalog explorer</title>
          <style>
            :root {
              color-scheme: light dark;
              --bg: #f8fafc;
              --panel: #ffffff;
              --text: #172033;
              --muted: #526071;
              --line: #d8dee8;
              --accent: #15616d;
              --accent-2: #7d4e24;
              --soft: #e9f5f6;
            }
            @media (prefers-color-scheme: dark) {
              :root {
                --bg: #11151c;
                --panel: #181f2a;
                --text: #edf2f7;
                --muted: #a6b0bf;
                --line: #2d3748;
                --accent: #5dc7d3;
                --accent-2: #f0b36a;
                --soft: #1b3238;
              }
            }
            * { box-sizing: border-box; }
            body {
              margin: 0;
              font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
              background: var(--bg);
              color: var(--text);
            }
            header {
              padding: 32px clamp(18px, 4vw, 56px) 18px;
              border-bottom: 1px solid var(--line);
              background: var(--panel);
            }
            main { padding: 28px clamp(18px, 4vw, 56px) 48px; }
            h1 { margin: 0 0 10px; font-size: clamp(2rem, 4vw, 4rem); letter-spacing: 0; }
            h2, h3 { letter-spacing: 0; }
            p { color: var(--muted); line-height: 1.55; }
            a { color: var(--accent); font-weight: 700; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .topline { color: var(--accent-2); font-weight: 800; text-transform: uppercase; font-size: .78rem; }
            .summary { max-width: 920px; font-size: 1.05rem; }
            .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
            .actions a {
              border: 1px solid var(--line);
              border-radius: 8px;
              padding: 10px 12px;
              background: var(--soft);
            }
            .grid {
              display: grid;
              gap: 14px;
              grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            }
            .layer-card, .object-card {
              background: var(--panel);
              border: 1px solid var(--line);
              border-radius: 8px;
              padding: 18px;
            }
            .kicker {
              color: var(--accent-2);
              font-size: .75rem;
              font-weight: 800;
              letter-spacing: 0;
              text-transform: uppercase;
            }
            .metrics, .chips, .row {
              display: flex;
              align-items: center;
              flex-wrap: wrap;
              gap: 8px;
            }
            .row { justify-content: space-between; }
            .metrics span, .chips span, .pill {
              border: 1px solid var(--line);
              border-radius: 999px;
              padding: 5px 8px;
              color: var(--muted);
              font-size: .82rem;
            }
            section { margin-top: 34px; }
            table {
              width: 100%;
              border-collapse: collapse;
              background: var(--panel);
              border: 1px solid var(--line);
              border-radius: 8px;
              overflow: hidden;
            }
            th, td {
              text-align: left;
              padding: 12px;
              border-bottom: 1px solid var(--line);
              vertical-align: top;
            }
            th { color: var(--muted); font-size: .82rem; }
            tr:last-child td { border-bottom: 0; }
            .table-wrap { overflow-x: auto; }
          </style>
        </head>
        <body>
          <header>
            <div class="topline">middle-core semantic service</div>
            <h1>Business Object Catalog</h1>
            <p class="summary">Typed business objects and scenario contracts for composing ArcadeDB capability services, platform operational services, and meta-services into agent-safe workflows.</p>
            <div class="actions">
              <a href="/health">Health JSON</a>
              <a href="/catalog">Catalog JSON</a>
              <a href="/objects/tool-offering">Tool Offering</a>
              <a href="/scenarios/read-only-query-lab">Read-only Query Lab</a>
            </div>
          </header>
          <main>
            <section>
              <h2>Service Families</h2>
              <div class="grid">{{layerCards}}</div>
            </section>
            <section>
              <h2>Business Objects</h2>
              <div class="grid">{{objectCards}}</div>
            </section>
            <section>
              <h2>Scenario Contracts</h2>
              <div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Scenario</th>
                      <th>Layers</th>
                      <th>Capabilities</th>
                      <th>MCP</th>
                      <th>Outputs</th>
                    </tr>
                  </thead>
                  <tbody>{{scenarioRows}}</tbody>
                </table>
              </div>
            </section>
          </main>
        </body>
        </html>
        """;
    }

    private static string Html(string value) => System.Net.WebUtility.HtmlEncode(value);
}
