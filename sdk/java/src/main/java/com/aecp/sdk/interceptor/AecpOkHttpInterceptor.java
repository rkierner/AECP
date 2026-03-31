package com.aecp.sdk.interceptor;

import com.aecp.sdk.AgentContext;
import com.aecp.sdk.events.ExecutionEvent;
import com.aecp.sdk.publisher.EventPublisher;
import okhttp3.Interceptor;
import okhttp3.Request;
import okhttp3.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.time.Instant;

/**
 * OkHttp interceptor that:
 * <ul>
 *   <li>Injects {@code X-Correlation-Id} and {@code X-Execution-Id} headers into outbound requests
 *   <li>Measures response latency
 *   <li>Emits an {@link ExecutionEvent} for every HTTP call
 * </ul>
 *
 * <p>Register on your OkHttpClient:
 * <pre>{@code
 * OkHttpClient client = new OkHttpClient.Builder()
 *     .addInterceptor(new AecpOkHttpInterceptor(agent.getPublisher(), "my-agent"))
 *     .build();
 * }</pre>
 */
public class AecpOkHttpInterceptor implements Interceptor {

    private static final Logger log = LoggerFactory.getLogger(AecpOkHttpInterceptor.class);

    private final EventPublisher publisher;
    private final String agentId;

    public AecpOkHttpInterceptor(EventPublisher publisher, String agentId) {
        this.publisher = publisher;
        this.agentId = agentId;
    }

    @Override
    public Response intercept(Chain chain) throws IOException {
        AgentContext.Context ctx = AgentContext.current();

        // Inject correlation headers for distributed tracing
        Request enrichedRequest = chain.request().newBuilder()
                .header("X-Correlation-Id", ctx.correlationId())
                .header("X-Execution-Id", ctx.executionId())
                .build();

        Instant start = Instant.now();
        String action = buildActionName(enrichedRequest);
        String executionId = ctx.executionId();
        String status = "success";
        String errorMessage = null;

        try {
            Response response = chain.proceed(enrichedRequest);
            if (!response.isSuccessful()) {
                status = "failure";
                errorMessage = "HTTP " + response.code();
            }
            return response;
        } catch (IOException ex) {
            status = "failure";
            errorMessage = ex.getMessage();
            throw ex;
        } finally {
            Instant end = Instant.now();
            long latencyMs = end.toEpochMilli() - start.toEpochMilli();

            ExecutionEvent event = new ExecutionEvent(agentId, executionId, start, action);
            event.setTimestampEnd(end);
            event.setStatus(status);
            event.setLatencyMs(latencyMs);
            event.setErrorMessage(errorMessage);
            event.setCorrelationId(ctx.correlationId());

            safePublish(event);
        }
    }

    /** Builds a dot-notation action name from the HTTP method and host. */
    private String buildActionName(Request request) {
        return "http." + request.method().toLowerCase() + "." + request.url().host();
    }

    private void safePublish(ExecutionEvent event) {
        try {
            publisher.publish(event);
        } catch (Exception ex) {
            log.warn("Failed to publish HTTP interceptor event: {}", ex.getMessage());
        }
    }
}
