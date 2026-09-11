using Microsoft.AspNetCore.Mvc;

namespace Gateway.Controllers;

/// <summary>
/// Health check endpoints for the API Gateway.
/// Used by Kubernetes liveness and readiness probes.
/// </summary>
[ApiController]
[Route("[controller]")]
public class HealthController : ControllerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<HealthController> _logger;

    public HealthController(IHttpClientFactory httpClientFactory, ILogger<HealthController> logger)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    /// <summary>
    /// Liveness probe — confirms the gateway is running.
    /// </summary>
    [HttpGet("/health")]
    public IActionResult Health()
    {
        return Ok(new
        {
            status = "healthy",
            service = "gateway",
            version = "1.0.0",
            environment = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT") ?? "Production",
            timestamp = DateTime.UtcNow
        });
    }

    /// <summary>
    /// Readiness probe — checks downstream service connectivity.
    /// </summary>
    [HttpGet("/ready")]
    public async Task<IActionResult> Ready()
    {
        var agentApiHealthy = await CheckServiceHealth("AgentApi", "/health");
        var evaluatorHealthy = await CheckServiceHealth("Evaluator", "/health");

        var isReady = agentApiHealthy && evaluatorHealthy;

        return isReady
            ? Ok(new { ready = true, agent_api = "connected", evaluator = "connected" })
            : StatusCode(503, new { ready = false, agent_api = agentApiHealthy ? "connected" : "disconnected", evaluator = evaluatorHealthy ? "connected" : "disconnected" });
    }

    private async Task<bool> CheckServiceHealth(string clientName, string path)
    {
        try
        {
            var client = _httpClientFactory.CreateClient(clientName);
            var response = await client.GetAsync(path);
            return response.IsSuccessStatusCode;
        }
        catch (Exception ex)
        {
            _logger.LogWarning("Health check failed for {Service}: {Error}", clientName, ex.Message);
            return false;
        }
    }
}
