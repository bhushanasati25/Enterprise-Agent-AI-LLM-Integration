using Microsoft.AspNetCore.Mvc;

namespace Gateway.Controllers;

/// <summary>
/// Proxied agent endpoints with gateway-level auth and logging.
/// These complement YARP for endpoints that need custom logic.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class AgentsController : ControllerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<AgentsController> _logger;

    public AgentsController(IHttpClientFactory httpClientFactory, ILogger<AgentsController> logger)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    /// <summary>
    /// Proxy agent invocation with gateway-level audit logging.
    /// </summary>
    [HttpPost("invoke")]
    public async Task<IActionResult> InvokeAgent()
    {
        var client = _httpClientFactory.CreateClient("AgentApi");

        _logger.LogInformation(
            "Agent invocation proxied | IP={ClientIP} | UserAgent={UserAgent}",
            HttpContext.Connection.RemoteIpAddress,
            Request.Headers.UserAgent.ToString()
        );

        try
        {
            // Forward the request body to the agent API
            using var requestContent = new StreamContent(Request.Body);
            requestContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/json");

            var response = await client.PostAsync("/api/agents/invoke", requestContent);
            var responseContent = await response.Content.ReadAsStringAsync();

            return Content(responseContent, "application/json");
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Failed to proxy agent invocation");
            return StatusCode(502, new { error = "Agent service unavailable", detail = ex.Message });
        }
        catch (TaskCanceledException)
        {
            _logger.LogWarning("Agent invocation timed out");
            return StatusCode(504, new { error = "Agent service timeout" });
        }
    }

    /// <summary>
    /// List available agent types.
    /// </summary>
    [HttpGet("types")]
    public async Task<IActionResult> ListAgentTypes()
    {
        var client = _httpClientFactory.CreateClient("AgentApi");

        try
        {
            var response = await client.GetAsync("/api/agents/types");
            var content = await response.Content.ReadAsStringAsync();
            return Content(content, "application/json");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to list agent types");
            return StatusCode(502, new { error = "Agent service unavailable" });
        }
    }
}
