import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: z.ZodTypeAny;
  inputJsonSchema: Record<string, unknown>;
  handler: (input: any) => Promise<unknown>;
}

export interface DefineToolSpec<S extends z.ZodTypeAny> {
  name: string;
  description: string;
  input: S;
  handler: (input: z.infer<S>) => Promise<unknown>;
}

export function defineTool<S extends z.ZodTypeAny>(
  spec: DefineToolSpec<S>,
): ToolDefinition {
  const jsonSchema = zodToJsonSchema(spec.input, {
    target: "jsonSchema7",
    $refStrategy: "none",
  }) as Record<string, unknown>;
  delete jsonSchema.$schema;

  return {
    name: spec.name,
    description: spec.description,
    inputSchema: spec.input,
    inputJsonSchema: jsonSchema,
    handler: spec.handler as (input: unknown) => Promise<unknown>,
  };
}
