FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

COPY templates/middle-core/MiddleCore.csproj ./MiddleCore.csproj
RUN dotnet restore ./MiddleCore.csproj

COPY templates/middle-core/ ./
COPY templates/business-object-catalog.example.json ./catalog.json
RUN dotnet publish ./MiddleCore.csproj --configuration Release --output /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
ENV ASPNETCORE_URLS=http://0.0.0.0:8001
ENV BUSINESS_OBJECT_CATALOG=/app/catalog.json

COPY --from=build /app/publish ./
COPY --from=build /src/catalog.json ./catalog.json

EXPOSE 8001
ENTRYPOINT ["dotnet", "MiddleCore.dll"]
