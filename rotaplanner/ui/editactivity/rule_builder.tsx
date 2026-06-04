import { createSignal, createMemo, For, Show } from "solid-js";

// Define what types of fields, operators, and rules our scheduling system supports
const FIELD_OPTIONS = [
  { value: "assignments.roles.supervisors.length", label: "Supervisor Count" },
  { value: "assignments.all.has_skill", label: "Staff Member Skill" },
];

const OPERATOR_OPTIONS = [
  { value: ">", label: "is greater than" },
  { value: "==", label: "equals" },
  { value: "contains", label: "has specific skill" },
];

interface RuleNode {
  id: string;
  type: "rule" | "group";
  parentId: string | null;
  // Group specific properties
  combinator?: "AND" | "OR";
  // Rule specific properties
  field?: string;
  operator?: string;
  value?: string;
}

export function RuleBuilder() {
  // We manage the entire tree as a flat array for trivial state mutations
  const [nodes, setNodes] = createSignal<RuleNode[]>([
    { id: "root", type: "group", combinator: "OR", parentId: null },
  ]);

  // Helper to generate unique IDs
  const generateId = () => Math.random().toString(36).substring(2, 9);

  // Add a simple rule criteria to a specific group
  const addRule = (groupId: string) => {
    setNodes([
      ...nodes(),
      {
        id: generateId(),
        type: "rule",
        parentId: groupId,
        field: FIELD_OPTIONS[0].value,
        operator: OPERATOR_OPTIONS[0].value,
        value: "0",
      },
    ]);
  };

  // Add a nested condition group (AND/OR block)
  const addGroup = (groupId: string) => {
    setNodes([
      ...nodes(),
      { id: generateId(), type: "group", combinator: "AND", parentId: groupId },
    ]);
  };

  // Delete a node and all of its cascading nested children
  const deleteNode = (id: string) => {
    if (id === "root") return; // Keep the base group intact

    let idsToDelete = new Set([id]);
    let count: number;

    // Iteratively find all sub-children
    do {
      count = idsToDelete.size;
      nodes().forEach((node) => {
        if (node.parentId && idsToDelete.has(node.parentId)) {
          idsToDelete.add(node.id);
        }
      });
    } while (idsToDelete.size !== count);

    setNodes(nodes().filter((node) => !idsToDelete.has(node.id)));
  };

  // Update specific values inside a node reactively
  const updateNode = (id: string, updates: Partial<RuleNode>) => {
    setNodes(
      nodes().map((node) => (node.id === id ? { ...node, ...updates } : node)),
    );
  };

  // Build a tree structure from our flat signals array for the final JSON output
  const jsonOutput = createMemo(() => {
    const buildTree = (parentId: string | null): any => {
      return nodes()
        .filter((n) => n.parentId === parentId)
        .map((n) => {
          if (n.type === "group") {
            return {
              type: "group",
              combinator: n.combinator,
              rules: buildTree(n.id),
            };
          }
          return {
            type: "rule",
            field: n.field,
            operator: n.operator,
            value: n.value,
          };
        });
    };
    return buildTree(null)[0];
  });

  // Recursive Group Renderer Component
  const GroupRenderer = (props: { groupId: string }) => {
    const currentGroup = () => nodes().find((n) => n.id === props.groupId);
    const children = () => nodes().filter((n) => n.parentId === props.groupId);

    return (
      <div
        style={{
          "border-left": "3px solid #cbd5e1",
          "padding-left": "16px",
          "margin-top": "12px",
        }}
      >
        <div
          style={{
            display: "flex",
            gap: "8px",
            "align-items": "center",
            "margin-bottom": "12px",
          }}
        >
          <select
            value={currentGroup()?.combinator}
            onChange={(e) =>
              updateNode(props.groupId, { combinator: e.target.value as any })
            }
            style={{ "font-weight": "bold", padding: "4px 8px" }}
          >
            <option value="OR">ANY (OR)</option>
            <option value="AND">ALL (AND)</option>
          </select>

          <button
            onClick={() => addRule(props.groupId)}
            style={{ padding: "4px 8px" }}
          >
            + Add Rule
          </button>
          <button
            onClick={() => addGroup(props.groupId)}
            style={{ padding: "4px 8px" }}
          >
            + Add Group
          </button>

          <Show when={props.groupId !== "root"}>
            <button
              onClick={() => deleteNode(props.groupId)}
              style={{ color: "red", padding: "4px 8px" }}
            >
              Delete Group
            </button>
          </Show>
        </div>

        <div
          style={{ display: "flex", "flex-direction": "column", gap: "8px" }}
        >
          <For each={children()}>
            {(node) => (
              <Show
                when={node.type === "group"}
                fallback={
                  <div
                    style={{
                      display: "flex",
                      gap: "8px",
                      "align-items": "center",
                      background: "#f8fafc",
                      padding: "8px",
                      "border-radius": "4px",
                    }}
                  >
                    <select
                      value={node.field}
                      onChange={(e) =>
                        updateNode(node.id, { field: e.target.value })
                      }
                    >
                      <For each={FIELD_OPTIONS}>
                        {(opt) => (
                          <option value={opt.value}>{opt.label}</option>
                        )}
                      </For>
                    </select>

                    <select
                      value={node.operator}
                      onChange={(e) =>
                        updateNode(node.id, { operator: e.target.value })
                      }
                    >
                      <For each={OPERATOR_OPTIONS}>
                        {(opt) => (
                          <option value={opt.value}>{opt.label}</option>
                        )}
                      </For>
                    </select>

                    <input
                      type="text"
                      value={node.value}
                      onInput={(e) =>
                        updateNode(node.id, { value: e.currentTarget.value })
                      }
                      style={{ padding: "4px", width: "150px" }}
                    />

                    <button
                      onClick={() => deleteNode(node.id)}
                      style={{
                        color: "red",
                        border: "none",
                        background: "none",
                        cursor: "pointer",
                      }}
                    >
                      ✕
                    </button>
                  </div>
                }
              >
                <GroupRenderer groupId={node.id} />
              </Show>
            )}
          </For>
        </div>
      </div>
    );
  };

  return (
    <div style={{ padding: "20px", "font-family": "sans-serif" }}>
      <h2>Roster Validation Rule Builder</h2>
      <GroupRenderer groupId="root" />

      <hr style={{ "margin-top": "24px" }} />
      <h3>Generated JSON Rule Payload (Sends to Python Backend):</h3>
      <pre
        style={{
          background: "#0f172a",
          color: "#38bdf8",
          padding: "16px",
          "border-radius": "6px",
          "overflow-x": "auto",
        }}
      >
        {JSON.stringify(jsonOutput(), null, 2)}
      </pre>
    </div>
  );
}
