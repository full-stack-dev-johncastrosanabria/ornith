Implement POST /orders in ASP.NET Core. Accept sku (nonblank), quantity (1..100 inclusive), unitPrice (>=0). Return HTTP 201 with JSON total = quantity * unitPrice for valid input, otherwise HTTP 400. Preserve public record signature.

Run: dotnet test tests/Acceptance.csproj --no-restore --disable-build-servers -p:UseSharedCompilation=false -v minimal
Do not modify tests or project dependency files.
