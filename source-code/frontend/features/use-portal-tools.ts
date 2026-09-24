"use client";
import { useEffect } from "react";
import { getState, type State } from "@/api";
type Tool = {
  name: string;
  title: string;
  description: string;
  inputSchema: object;
  annotations: { readOnlyHint: boolean; untrustedContentHint: boolean };
  execute: (input: unknown) => Promise<unknown>;
};
type ToolDocument = Document & {
  modelContext?: {
    registerTool: (tool: Tool, options: { signal: AbortSignal }) => void | Promise<void>;
  };
};
export function usePortalTools(userId: string | undefined) {
  useEffect(() => {
    const context = (document as ToolDocument).modelContext;
    if (!userId || !context?.registerTool) return;
    const lifecycle = new AbortController();
    const tool: Tool = {
      name: "get_learning_summary",
      title: "Read learner progress",
      description:
        "Read progress for the signed-in child, or a specified child when signed in as a parent. Uses the same authorised records as My progress.",
      inputSchema: {
        type: "object",
        properties: { studentId: { type: "string" } },
        additionalProperties: false,
      },
      annotations: { readOnlyHint: true, untrustedContentHint: true },
      async execute(input) {
        if (
          !input ||
          typeof input !== "object" ||
          Array.isArray(input) ||
          Object.keys(input).some((k) => k !== "studentId")
        )
          throw new Error("Expected an object with optional studentId.");
        if ("studentId" in input && typeof input.studentId !== "string")
          throw new Error("studentId must be a string.");
        const state: State = await getState();
        const id = "studentId" in input ? input.studentId : state.user.id;
        const child = state.students.find((s) => s.id === id);
        if (!child) throw new Error("Student is not available to this account.");
        const attempts = state.attempts.filter((a) => a.studentId === child.id);
        return {
          student: { id: child.id, name: child.name, grade: child.grade },
          attempts: attempts.length,
          awaitingReview: attempts.filter((a) => a.status === "needs-review").length,
          assessed: attempts.filter((a) => a.mark !== null).length,
          subjects: child.subjects.map((id) => ({
            subject: id,
            qualification: child.courses[id]?.level,
            attempts: attempts.filter((a) => a.subject === id).length,
          })),
        };
      },
    };
    try {
      void Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal })).catch(
        () => {},
      );
    } catch {
      /* Optional browser capability; the portal works without it. */
    }
    return () => lifecycle.abort();
  }, [userId]);
}
