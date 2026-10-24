using System.Net;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;
public class OrdersTests : IClassFixture<WebApplicationFactory<Program>> {
 readonly HttpClient client;
 public OrdersTests(WebApplicationFactory<Program> app) { client=app.CreateClient(); }
 [Fact] public async Task ValidOrder() {
 var r=await client.PostAsJsonAsync("/orders",new {sku="ABC",quantity=3,unitPrice=2.50m});
 Assert.Equal(HttpStatusCode.Created,r.StatusCode);
 var j=await r.Content.ReadFromJsonAsync<System.Text.Json.JsonElement>();
 Assert.Equal(7.50m,j.GetProperty("total").GetDecimal());
 }
 [Theory] [InlineData("",1,2)] [InlineData(" ",1,2)] [InlineData("A",0,2)] [InlineData("A",101,2)] [InlineData("A",1,-1)]
 public async Task InvalidOrder(string sku,int quantity,decimal unitPrice) {
 var r=await client.PostAsJsonAsync("/orders",new {sku,quantity,unitPrice});Assert.Equal(HttpStatusCode.BadRequest,r.StatusCode);
 }
}
