Implement PUT /products/{id} in the ASP.NET Core API (src/) following the contract in README.md, with optimistic concurrency on version, so the acceptance tests pass.

Run: dotnet test tests/Acceptance.csproj --no-restore --disable-build-servers -p:UseSharedCompilation=false -p:EnableSourceControlManagerQueries=false -p:EnableSourceLink=false -v minimal
Do not modify tests or project dependency files.
