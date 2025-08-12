# graph_generate_org_chart_fixed.py
from datetime import datetime, timezone
import asyncio
from dotenv import load_dotenv
import os
import time

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.driver.falkordb_driver import FalkorDriver

# load env
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY in your environment")

# FalkorDB connection (adjust if needed)
falkor_host = os.getenv("FALKORDB_HOST", "localhost")
falkor_port = int(os.getenv("FALKORDB_PORT", "6379"))
falkor_username = os.getenv("FALKORDB_USERNAME", None)
falkor_password = os.getenv("FALKORDB_PASSWORD", None)

GROUP_ID = "org_chart_demo"  # keep same group for all episodes

async def main():
    driver = FalkorDriver(
        host=falkor_host,
        port=falkor_port,
        username=falkor_username,
        password=falkor_password
    )
    graphiti = Graphiti(graph_driver=driver)

    try:
        # 0) Clear previous graph (start clean)
        print(">>> Deleting any existing graph data (if present)...")
        try:
            await graphiti.delete_graph()
            print(">>> Previous graph removed.")
        except Exception as e:
            # some drivers may throw if graph doesn't exist — continue
            print(f" (delete_graph() raised: {e}) — continuing")

        # 1) Build indices & constraints (ensures RediSearch fields exist)
        print(">>> Building indices & constraints...")
        await graphiti.build_indices_and_constraints()
        print(">>> Indices ready.")

        # 2) Ingest the simple sentence-per-relation episodes
        print(">>> Ingesting simple relation episodes...")
        episodes = [
            ("alice_manages_thomas", "Alice is the manager of Thomas."),
            ("thomas_manages_bob",   "Thomas is the manager of Bob."),
            ("bob_manages_mark",     "Bob is the manager of Mark."),
            ("george_under_alice",   "George reports to Alice."),
            ("george_manages_mark",  "George is the manager of Mark."),
        ]

        now = datetime.now(timezone.utc)
        for name, text in episodes:
            print(f"  - adding episode: {name}")
            await graphiti.add_episode(
                name=name,
                episode_body=text,
                source=EpisodeType.text,
                source_description="org chart import",
                reference_time=now,
                group_id=GROUP_ID,
            )

        # 3) Add a single summary episode with explicit natural-language context
        #    This helps the retriever + LLM produce direct answers because it
        #    provides a compact description the LLM can use as supporting context.
        summary_text = (
            "Organization summary: Alice is the manager of Thomas. "
            "Thomas is the manager of Bob. Bob manages Mark. "
            "George reports to Alice and is also the manager of Mark. "
            "So the management lines are: Alice -> Thomas -> Bob -> Mark, "
            "and George -> Mark; George also reports to Alice in some contexts."
        )
        print(">>> Adding a compact summary episode to improve retrieval/LLM answers...")
        await graphiti.add_episode(
            name="org_summary",
            episode_body=summary_text,
            source=EpisodeType.text,
            source_description="org chart summary",
            reference_time=now,
            group_id=GROUP_ID,
        )

        print(">>> Waiting briefly to allow async ingestion to finish...")
        # Graphiti runs async calls internally — small pause helps ensure indexing has time.
        # Not strictly required, but useful in development to avoid racing the next step.
        time.sleep(2)

        print(">>> Ingestion finished. Your graph now contains only the org-chart data.")
        print("You can now run queries like: 'How is George related to Alice?' using Graphiti.")

    finally:
        await graphiti.close()
        await driver.close()
        print(">>> Connection closed.")

if __name__ == "__main__":
    asyncio.run(main())
