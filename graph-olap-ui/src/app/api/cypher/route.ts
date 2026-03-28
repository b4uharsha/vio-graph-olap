import { SYSTEM_PROMPT } from "@/lib/cypher-ai";
import { getDemoResponse } from "@/components/query-assistant/demo-responses";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { question } = body;

    if (!question || typeof question !== "string") {
      return Response.json(
        { error: "Missing or invalid 'question' field" },
        { status: 400 }
      );
    }

    const apiKey = process.env.ANTHROPIC_API_KEY;

    // If no API key, return demo response
    if (!apiKey || apiKey === "your-api-key-here") {
      const demo = getDemoResponse(question);
      return Response.json({
        cypher: demo.cypher,
        explanation: demo.explanation,
        isDemo: true,
      });
    }

    // Use Anthropic API via AI SDK
    const { generateText } = await import("ai");
    const { createAnthropic } = await import("@ai-sdk/anthropic");

    const anthropic = createAnthropic({ apiKey });

    const { text } = await generateText({
      model: anthropic("claude-sonnet-4-6"),
      system: SYSTEM_PROMPT,
      prompt: question,
      maxOutputTokens: 1024,
    });

    // Clean up the response — strip markdown fences if present
    let cypher = text.trim();
    if (cypher.startsWith("```")) {
      cypher = cypher.replace(/^```(?:cypher)?\n?/, "").replace(/\n?```$/, "");
    }

    // Generate explanation in a second call
    const { text: explanation } = await generateText({
      model: anthropic("claude-sonnet-4-6"),
      system:
        "You are a helpful assistant. Given a Cypher query and the original question, provide a brief 1-2 sentence explanation of what the query does. Be concise.",
      prompt: `Question: ${question}\n\nCypher query:\n${cypher}`,
      maxOutputTokens: 256,
    });

    return Response.json({
      cypher,
      explanation: explanation.trim(),
      isDemo: false,
    });
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : "An unexpected error occurred";

    // Check for common API errors
    if (message.includes("401") || message.includes("authentication")) {
      return Response.json(
        { error: "Invalid API key. Check your ANTHROPIC_API_KEY." },
        { status: 401 }
      );
    }

    if (message.includes("429") || message.includes("rate")) {
      return Response.json(
        { error: "Rate limit exceeded. Please try again in a moment." },
        { status: 429 }
      );
    }

    console.error("Cypher generation error:", error);
    return Response.json(
      { error: "Failed to generate Cypher query. " + message },
      { status: 500 }
    );
  }
}
