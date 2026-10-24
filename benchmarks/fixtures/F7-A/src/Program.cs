var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
app.MapPost("/orders", (Order order) => Results.StatusCode(501));
app.Run();
public record Order(string? Sku, int Quantity, decimal UnitPrice);
public partial class Program { }
