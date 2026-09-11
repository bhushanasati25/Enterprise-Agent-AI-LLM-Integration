using System.Text;
using System.Threading.RateLimiting;
using Gateway.Middleware;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;

var builder = WebApplication.CreateBuilder(args);

// ---------------------------------------------------------------------------
// Services
// ---------------------------------------------------------------------------

// YARP Reverse Proxy
builder.Services.AddReverseProxy()
    .LoadFromConfig(builder.Configuration.GetSection("ReverseProxy"));

// JWT Authentication
var jwtSettings = builder.Configuration.GetSection("Jwt");
var secretKey = jwtSettings["SecretKey"] ?? "your-256-bit-secret-key-change-in-production";

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey)),
            ValidateIssuer = true,
            ValidIssuer = jwtSettings["Issuer"] ?? "enterprise-ai-gateway",
            ValidateAudience = true,
            ValidAudience = jwtSettings["Audience"] ?? "enterprise-ai-services",
            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromMinutes(5)
        };

        // Allow unauthenticated access in Development
        if (builder.Environment.IsDevelopment())
        {
            options.Events = new JwtBearerEvents
            {
                OnAuthenticationFailed = context =>
                {
                    // Don't fail in development — log and continue
                    context.NoResult();
                    return Task.CompletedTask;
                }
            };
        }
    });

builder.Services.AddAuthorization();

// Rate Limiting
var rateLimitConfig = builder.Configuration.GetSection("RateLimiting");
var requestsPerMinute = rateLimitConfig.GetValue<int>("RequestsPerMinute", 100);
var burst = rateLimitConfig.GetValue<int>("Burst", 20);

builder.Services.AddRateLimiter(options =>
{
    options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(context =>
        RateLimitPartition.GetTokenBucketLimiter(
            partitionKey: context.Connection.RemoteIpAddress?.ToString() ?? "anonymous",
            factory: _ => new TokenBucketRateLimiterOptions
            {
                TokenLimit = burst,
                ReplenishmentPeriod = TimeSpan.FromMinutes(1),
                TokensPerPeriod = requestsPerMinute,
                AutoReplenishment = true,
                QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
                QueueLimit = 5
            }));

    options.OnRejected = async (context, token) =>
    {
        context.HttpContext.Response.StatusCode = 429;
        await context.HttpContext.Response.WriteAsJsonAsync(new
        {
            error = "Rate limit exceeded",
            retry_after_seconds = 60
        }, token);
    };
});

// CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        if (builder.Environment.IsDevelopment())
        {
            policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader();
        }
    });
});

builder.Services.AddControllers();
builder.Services.AddHttpClient("AgentApi", client =>
{
    client.BaseAddress = new Uri(builder.Configuration["AgentApi:BaseUrl"] ?? "http://agent-api:8000");
    client.Timeout = TimeSpan.FromSeconds(120);
});
builder.Services.AddHttpClient("Evaluator", client =>
{
    client.BaseAddress = new Uri(builder.Configuration["Evaluator:BaseUrl"] ?? "http://llm-evaluator:8001");
    client.Timeout = TimeSpan.FromSeconds(300);
});

// ---------------------------------------------------------------------------
// App Pipeline
// ---------------------------------------------------------------------------

var app = builder.Build();

// Request logging middleware
app.UseMiddleware<RequestLoggingMiddleware>();

app.UseCors();
app.UseRateLimiter();

// Authentication & Authorization (skip for health endpoints)
app.UseWhen(
    context => !context.Request.Path.StartsWithSegments("/health"),
    appBuilder =>
    {
        appBuilder.UseAuthentication();
        appBuilder.UseAuthorization();
    });

app.MapControllers();
app.MapReverseProxy();

app.Run();
