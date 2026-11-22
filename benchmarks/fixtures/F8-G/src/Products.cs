public record ProductInput(string? Name, decimal Price, int Stock, int? Version);

public record Product(int Id, string Name, decimal Price, int Stock, int Version);

public class ProductStore
{
    private readonly object gate = new();
    private readonly Dictionary<int, Product> products = new();
    private int nextId = 1;

    public Product? Find(int id)
    {
        lock (gate) return products.GetValueOrDefault(id);
    }

    public Product Add(ProductInput input)
    {
        lock (gate)
        {
            var product = new Product(nextId++, input.Name!.Trim(), input.Price, input.Stock, 1);
            products[product.Id] = product;
            return product;
        }
    }
}

public static class ProductValidation
{
    public static Dictionary<string, string[]> Validate(ProductInput input)
    {
        var errors = new Dictionary<string, string[]>();
        if (string.IsNullOrWhiteSpace(input.Name) || input.Name.Trim().Length > 80)
            errors["name"] = ["Name is required and has at most 80 characters."];
        if (input.Price < 0)
            errors["price"] = ["Price must not be negative."];
        if (input.Stock is < 0 or > 10000)
            errors["stock"] = ["Stock must be between 0 and 10000."];
        return errors;
    }
}
