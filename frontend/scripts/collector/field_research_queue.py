
#!/usr/bin/env python3
"""FIELD//BASE official-site review queue.

Starts the existing unified Research Manager with a queue interface.
The existing CSV validation, backups, and save endpoints remain unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path

COLLECTOR_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(COLLECTOR_DIR))

import field_location_reviewer as manager


QUEUE_UI = r"""
<style>
  .queue-toolbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
    padding: 15px;
    margin-bottom: 18px;
    background: #1b1f22;
    border: 1px solid #343a3f;
    border-radius: 12px;
  }

  .queue-toolbar button {
    border: 1px solid #66756f;
  }

  .queue-toolbar button.active {
    background: #dce8e4;
    color: #14201d;
  }

  .queue-progress {
    flex: 1;
    min-width: 200px;
    font-size: 14px;
    line-height: 1.6;
  }

  .queue-progress strong {
    color: #a8d6c6;
  }

  .queue-help {
    width: 100%;
    color: #aab2b9;
    font-size: 12px;
  }
</style>

<script>
(() => {
  "use strict";

  const controls = document.querySelector(".controls");

  const toolbar = document.createElement("div");
  toolbar.className = "queue-toolbar";

  const queueButton = document.createElement("button");
  queueButton.type = "button";
  queueButton.textContent = "公式URL未確認キュー";

  const allButton = document.createElement("button");
  allButton.type = "button";
  allButton.textContent = "通常表示";

  const progress = document.createElement("div");
  progress.className = "queue-progress";
  progress.setAttribute("role", "status");

  const help = document.createElement("div");
  help.className = "queue-help";
  help.textContent =
    "公式サイトを目視確認してURLを保存すると、次の未確認施設へ自動で進みます。";

  toolbar.append(
    queueButton,
    allButton,
    progress,
    help
  );

  controls.parentNode.insertBefore(
    toolbar,
    controls
  );

  const originalUpdateStats = updateStats;

  updateStats = function () {
    originalUpdateStats();

    const done = fields.filter(
      officialVerified
    ).length;

    const remaining = fields.length - done;

    progress.textContent = "";

    const label = document.createElement("strong");

    label.textContent =
      `${done} / ${fields.length} 件確認済み`;

    progress.append(
      label,
      `　残り ${remaining} 件`
    );
  };

  function syncButtons() {
    const inQueue =
      el("filter").value === "officialPending";

    queueButton.classList.toggle(
      "active",
      inQueue
    );

    allButton.classList.toggle(
      "active",
      !inQueue
    );
  }

  function setMode(mode) {
    el("filter").value = mode;
    el("search").value = "";

    selectedId = null;

    refreshSelection();
    syncButtons();
  }

  queueButton.addEventListener(
    "click",
    () => {
      setMode("officialPending");
    }
  );

  allButton.addEventListener(
    "click",
    () => {
      setMode("all");
    }
  );

  el("filter").addEventListener(
    "change",
    syncButtons
  );

  // After a successful official URL save,
  // the existing manager updates the field
  // and calls refreshSelection().
  //
  // The saved field no longer matches
  // officialPending, so the next pending
  // facility is selected automatically.

  setMode("officialPending");
  updateStats();
})();
</script>
"""


original_render_page = manager.render_page


def render_queue_page() -> str:
    html = original_render_page()

    marker = "</body>"

    if marker not in html:
        raise ValueError(
            "Research ManagerのHTML構造が想定と異なります"
        )

    return html.replace(
        marker,
        QUEUE_UI + "\n" + marker,
        1,
    )


def main() -> None:
    manager.render_page = render_queue_page

    print(
        "FIELD//BASE Official URL Review Queue"
    )

    manager.main()


if __name__ == "__main__":
    main()
