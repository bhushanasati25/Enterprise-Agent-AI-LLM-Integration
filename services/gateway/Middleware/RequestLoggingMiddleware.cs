using System.Diagnostics;

namespace Gateway.Middleware;

/// <summary>
/// Structured request logging middleware.
/// Logs all incoming requests with method, path, status code, and duration.
/// </summary>
public class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestLoggingMiddleware> _logger;

    public RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var stopwatch = Stopwatch.StartNew();
        var method = context.Request.Method;
        var path = context.Request.Path;
        var clientIp = context.Connection.RemoteIpAddress?.ToString() ?? "unknown";

        try
        {
            await _next(context);
        }
        finally
        {
            stopwatch.Stop();
            var statusCode = context.Response.StatusCode;
            var duration = stopwatch.ElapsedMilliseconds;

            // Skip logging for health check endpoints to reduce noise
            if (!path.StartsWithSegments("/health") && !path.StartsWithSegments("/ready"))
            {
                _logger.LogInformation(
                    "HTTP {Method} {Path} → {StatusCode} ({Duration}ms) | IP: {ClientIP}",
                    method, path, statusCode, duration, clientIp
                );
            }
        }
    }
}
