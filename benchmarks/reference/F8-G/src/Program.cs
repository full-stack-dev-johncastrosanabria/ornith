var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton<ProductStore>();
var app = builder.Build();

app.MapGet("/products/{id:int}", (int id, ProductStore store) =>
    store.Find(id) is { } product ? Results.Ok(product) : Results.NotFound());

app.MapPost("/products", (ProductInput input, ProductStore store) =>
{
    var errors = ProductValidation.Validate(input);
    if (errors.Count > 0) return Results.ValidationProblem(errors);
    var product = store.Add(input);
    return Results.Created($"/products/{product.Id}", product);
});

// Update contract: see README.md.
app.MapPut("/products/{id:int}", (int id, ProductInput input, ProductStore store) =>
{
    if (store.Find(id) is null) return Results.NotFound();
    var errors = ProductValidation.Validate(input);
    if (input.Version is null) errors["version"] = ["Version is required."];
    if (errors.Count > 0) return Results.ValidationProblem(errors);
    var (outcome, product) = store.Update(id, input);
    return outcome switch
    {
        UpdateOutcome.Updated => Results.Ok(product),
        UpdateOutcome.NotFound => Results.NotFound(),
        _ => Results.Conflict(),
    };
});

app.Run();

public partial class Program { }
