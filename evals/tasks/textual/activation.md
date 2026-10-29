# Textual activation cases

Judge semantic selection, not keyword matching. Do not tell the agent the skill
name.

## Should activate

1. "Our Textual DataTable flickers and the selected row jumps whenever the
   refresh timer fires. Make updates incremental and preserve selection."
2. "The detail pane wraps text one character per line after we switch tabs. It
   only happens when the pane was hidden during an update."

## Should not activate

1. "Make our marketing website responsive on mobile and improve its Lighthouse
   score."
2. "Write a SQL migration that adds an index to the orders table."

Expected: cases 1 and 2 select `textual-tui-engineering`; cases 3 and 4 do not.
