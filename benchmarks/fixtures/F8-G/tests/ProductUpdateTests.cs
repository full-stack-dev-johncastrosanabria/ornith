using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;

public class ProductUpdateTests : IClassFixture<WebApplicationFactory<Program>>
{
    readonly HttpClient client;

    public ProductUpdateTests(WebApplicationFactory<Program> app) { client = app.CreateClient(); }

    async Task<int> Create(string name = "Lamp", decimal price = 10m, int stock = 5)
    {
        var r = await client.PostAsJsonAsync("/products", new { name, price, stock });
        Assert.Equal(HttpStatusCode.Created, r.StatusCode);
        return (await r.Content.ReadFromJsonAsync<JsonElement>()).GetProperty("id").GetInt32();
    }

    Task<JsonElement> Get(int id) => client.GetFromJsonAsync<JsonElement>($"/products/{id}");

    [Fact]
    public async Task UpdateReplacesFieldsAndBumpsVersion()
    {
        var id = await Create();
        var r = await client.PutAsJsonAsync($"/products/{id}", new { name = "  Desk lamp ", price = 12.5m, stock = 4, version = 1 });
        Assert.Equal(HttpStatusCode.OK, r.StatusCode);
        var j = await r.Content.ReadFromJsonAsync<JsonElement>();
        Assert.Equal(id, j.GetProperty("id").GetInt32());
        Assert.Equal("Desk lamp", j.GetProperty("name").GetString());
        Assert.Equal(12.5m, j.GetProperty("price").GetDecimal());
        Assert.Equal(4, j.GetProperty("stock").GetInt32());
        Assert.Equal(2, j.GetProperty("version").GetInt32());
        var stored = await Get(id);
        Assert.Equal("Desk lamp", stored.GetProperty("name").GetString());
        Assert.Equal(2, stored.GetProperty("version").GetInt32());
    }

    [Fact]
    public async Task BoundaryValuesAreAccepted()
    {
        var id = await Create();
        var r = await client.PutAsJsonAsync($"/products/{id}", new { name = new string('n', 80), price = 0m, stock = 10000, version = 1 });
        Assert.Equal(HttpStatusCode.OK, r.StatusCode);
    }

    [Fact]
    public async Task MissingProductIsNotFound()
    {
        var r = await client.PutAsJsonAsync("/products/987654", new { name = "Lamp", price = 1m, stock = 1, version = 1 });
        Assert.Equal(HttpStatusCode.NotFound, r.StatusCode);
    }

    [Theory]
    [InlineData("", 1.0, 1)]
    [InlineData("   ", 1.0, 1)]
    [InlineData("TOO-LONG", 1.0, 1)]
    [InlineData("Lamp", -0.01, 1)]
    [InlineData("Lamp", 1.0, -1)]
    [InlineData("Lamp", 1.0, 10001)]
    public async Task InvalidUpdateIsRejectedAndChangesNothing(string name, double price, int stock)
    {
        var id = await Create();
        if (name == "TOO-LONG") name = new string('x', 81);
        var r = await client.PutAsJsonAsync($"/products/{id}", new { name, price = (decimal)price, stock, version = 1 });
        Assert.Equal(HttpStatusCode.BadRequest, r.StatusCode);
        var stored = await Get(id);
        Assert.Equal("Lamp", stored.GetProperty("name").GetString());
        Assert.Equal(1, stored.GetProperty("version").GetInt32());
    }

    [Fact]
    public async Task MissingVersionIsBadRequest()
    {
        var id = await Create();
        var r = await client.PutAsJsonAsync($"/products/{id}", new { name = "Lamp", price = 1m, stock = 1 });
        Assert.Equal(HttpStatusCode.BadRequest, r.StatusCode);
    }

    [Fact]
    public async Task StaleVersionIsConflict()
    {
        var id = await Create();
        var first = await client.PutAsJsonAsync($"/products/{id}", new { name = "First", price = 1m, stock = 1, version = 1 });
        Assert.Equal(HttpStatusCode.OK, first.StatusCode);
        var second = await client.PutAsJsonAsync($"/products/{id}", new { name = "Second", price = 2m, stock = 2, version = 1 });
        Assert.Equal(HttpStatusCode.Conflict, second.StatusCode);
        var stored = await Get(id);
        Assert.Equal("First", stored.GetProperty("name").GetString());
        Assert.Equal(2, stored.GetProperty("version").GetInt32());
    }

    [Fact]
    public async Task CreateStillValidates()
    {
        var r = await client.PostAsJsonAsync("/products", new { name = " ", price = 1m, stock = 1 });
        Assert.Equal(HttpStatusCode.BadRequest, r.StatusCode);
    }
}
