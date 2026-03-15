from lxml import html
from xmldiff import main
import logging

from datastar_py import ServerSentEventGenerator


class DatastarDiffEngine:
    def __init__(self, dummy_id="DUMMY_ROOT"):
        self.dummy_id = dummy_id

    def _get_stable_selector(self, node):
        """
        Climbs the tree to find the nearest stable ID or returns a specific CSS path.
        """
        parts = []
        current = node
        while current is not None:
            # Check for ID - this is our most stable anchor
            node_id = current.get("id")
            if node_id and node_id != self.dummy_id:
                parts.insert(0, f"#{node_id}")
                return " > ".join(parts)

            # Stop at dummy root
            if current.get("id") == self.dummy_id:
                break

            tag = current.tag
            parent = current.getparent()
            if parent is not None:
                # Calculate nth-of-type index
                siblings = [s for s in parent if s.tag == tag]
                if len(siblings) > 1:
                    index = siblings.index(current) + 1
                    parts.insert(0, f"{tag}:nth-of-type({index})")
                else:
                    parts.insert(0, tag)
            else:
                parts.insert(0, tag)
            current = current.getparent()

        return " > ".join(parts) if parts else "*"

    def generate_patch(self, old_html: str, new_html: str) -> str:
        """
        Compares two HTML fragments and returns Datastar-compatible SSE events.
        """
        if not old_html or not new_html:
            return ""

        # 1. Prepare Trees (Wrapped to ensure single-root fragments)
        old_tree = html.fromstring(old_html)
        new_tree = html.fromstring(new_html)

        try:
            actions = main.diff_trees(old_tree, new_tree)
        except Exception as e:
            logging.error(f"Diff failed: {e}")
            return ""

        events = []
        processed_selectors = set()

        for action in actions:
            action_name = type(action).__name__

            # --- HANDLE DELETIONS ---
            if action_name == "DeleteNode":
                try:
                    # Target exists in OLD tree
                    target_node = old_tree.xpath(action.node)[0]
                    selector = self._get_stable_selector(target_node)

                    # Remove from browser via script
                    events.append(ServerSentEventGenerator.remove_elements(selector))
                except Exception:
                    logging.error(
                        f"Failed to handle DeleteNode action: {action} because {e}"
                    )
                    continue

            # --- HANDLE MOVES / REORDERS ---
            elif action_name == "MoveNode":
                try:
                    # Get the parent of the node in the NEW tree to refresh the order
                    target_node = new_tree.xpath(action.node)[0]
                    parent_node = target_node.getparent()
                    selector = self._get_stable_selector(parent_node)

                    if selector in processed_selectors:
                        continue

                    fragment = html.tostring(parent_node, encoding="unicode").strip()
                    events.append(
                        "event: datastar-fragment\n"
                        f"data: selector {selector}\n"
                        f"data: fragment {fragment}\n\n"
                    )
                    processed_selectors.add(selector)
                except Exception as e:
                    logging.error(
                        f"Failed to handle MoveNode action: {action} because {e}"
                    )
                    continue

            # --- HANDLE UPDATES & INSERTS ---
            elif action_name in [
                "UpdateNode",
                "InsertNode",
                "UpdateAttrib",
                "UpdateTextIn",
            ]:
                path = getattr(action, "node", None)
                if not path:
                    continue

                try:
                    target_node = new_tree.xpath(path)[0]
                    selector = self._get_stable_selector(target_node)

                    if selector in processed_selectors or not selector:
                        continue

                    fragment = html.tostring(target_node, encoding="unicode").strip()
                    events.append(
                        ServerSentEventGenerator.patch_elements(fragment, selector)
                    )
                    processed_selectors.add(selector)
                except Exception as e:
                    logging.error(
                        f"Failed to handle {action_name} action: {action} because {e}"
                    )
                    continue
            else:
                logging.warning(f"Unhandled action type: {action_name} - {action}")

        return "".join(events)


diffengine = DatastarDiffEngine()

print(
    diffengine.generate_patch(
        '<html><body><div id="container1"><span id="user">Alice</span><span id="moves">Wah</span><div id="score">10</div></div><div id="container2"></div></body></html>',
        '<html><body><div id="container1"><span id="user">Alice</span><div id="score">25</div></div><div id="container2"><span id="moves">Wah</span></div></body></html>',
    )
)
