import { AgentEvent } from "@/types";

type AgentActivityProps = {
  events: AgentEvent[];
};

export default function AgentActivity({ events }: AgentActivityProps) {
  if (!events.length) {
    return null;
  }

  return (
    <div className="mb-4 rounded-lg border bg-gray-50 p-4">
      <div className="mb-3 text-sm font-semibold text-gray-700">
        Agent Activity
      </div>

      <div className="space-y-2">
        {events.map((event, index) => {
          if (event.type === "TOOL_START") {
            return (
              <div
                key={index}
                className="flex items-center gap-2 text-sm text-gray-600"
              >
                <span>🔍</span>

                <span>
                  Using <strong>{event.tool}</strong>
                </span>
              </div>
            );
          }

          if (event.type === "TOOL_RESULT") {
            return (
              <div
                key={index}
                className="flex items-center gap-2 text-sm text-gray-600"
              >
                <span>✓</span>

                <span>{event.message}</span>
              </div>
            );
          }

          if (event.type === "ERROR") {
            return (
              <div key={index} className="text-sm text-red-600">
                ❌ {event.message}
              </div>
            );
          }

          return null;
        })}
      </div>
    </div>
  );
}
