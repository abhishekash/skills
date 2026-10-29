# Status activation cases

Judge semantic selection, not keyword matching. Do not tell the agent the skill
name.

## Should activate

1. "Our monitor shows a session as completed even though a new turn just started.
   How should we model session vs turn status?"
2. "The app says my agent is stuck after 35 seconds without output. I need to
   distinguish quiet work, an approval wait, and a collector delay."

## Should not activate

1. "Add a retry button to the job details screen."
2. "Write a SQL query that counts completed jobs per day."

Expected: cases 1 and 2 select `agent-session-status`; cases 3 and 4 do not.
