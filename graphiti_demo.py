from datetime import datetime, timezone
import asyncio
# Graphiti + FalkorDB imports
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.driver.falkordb_driver import FalkorDriver
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
from dotenv import load_dotenv
import os

load_dotenv()

falkor_username = os.environ.get('FALKORDB_USERNAME', None)
falkor_password = os.environ.get('FALKORDB_PASSWORD', None)
falkor_host = os.environ.get('FALKORDB_HOST', 'localhost')
falkor_port = os.environ.get('FALKORDB_PORT', '6379')
OPENAI_KEY  = os.environ.get("OPENAI_API_KEY")

if not OPENAI_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY in your environment")

async def main():
    # 1) Connect driver + Graphiti
    driver = FalkorDriver(host=falkor_host, port=falkor_port, username=falkor_username, password=falkor_password)
    graphiti = Graphiti(graph_driver=driver)

    try:
        # 2) Build indices & constraints (only needs to be done once on a fresh DB)
        print(">>> building indices & constraints (this may take a few seconds)...")
        await graphiti.build_indices_and_constraints()

        # -------------------------
        # STEP A — initial ingestion
        # -------------------------
        print(">>> adding initial episodes (one-time load)...")
        episodes = [
            {
                "name": "initial_1",
                "episode_body": "Alice is a data scientist in New York who joined ACME in 2024.",
                "source": EpisodeType.text,
                "source_description": "initial import",
                "reference_time": datetime.now(timezone.utc),
                "group_id": "demo_group"
            },
            {
                "name": "initial_2",
                "episode_body": "Bob is a ML Engineer in San Francisco who joined ACME in 2024.",
                "source": EpisodeType.text,
                "source_description": "initial import",
                "reference_time": datetime.now(timezone.utc),
                "group_id": "demo_group"
            }
        ]

        for ep in episodes:
            await graphiti.add_episode(
                name=ep["name"],
                episode_body=ep["episode_body"],
                source=ep["source"],
                source_description=ep["source_description"],
                reference_time=ep["reference_time"],
                group_id=ep["group_id"],
            )
        print(">>> initial ingestion complete")
                # -------------
        # STEP B — query
        # -------------
        query = "Who is the Data Scientist?"
        print(f"\n>>> Searching for: {query!r}")
        # simple high-level hybrid search (Graphiti combines embeddings + full-text + rerank)
        search_results = await graphiti.search(query)
        print("Search results (raw):")
        print(search_results)  # inspect what Graphiti returns

        # If you want node-specific hybrid search using a recipe:
        print("\n>>> NODE search (recipe NODE_HYBRID_SEARCH_RRF)")
        node_cfg = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        node_cfg.limit = 5
        node_results = await graphiti._search(query=query, config=node_cfg)
        print(node_results)

        # ------------------------------
        # STEP C — later: ingest more data
        # ------------------------------
        print("\n>>> ingesting additional episode (incremental)...")
        await graphiti.add_episode(
            name="later_1",
            episode_body="Charlie joined ACME as a Product Manager in 2025 and collaborates with Alice.",
            source=EpisodeType.text,
            source_description="late import",
            reference_time=datetime.now(timezone.utc),
            group_id="demo_group"
        )
        print(">>> additional ingestion complete")

        # query again to see updated answers
        query2 = "Who works with Alice at ACME?"
        print(f"\n>>> Searching for: {query2!r}")
        updated_results = await graphiti.search(query2)
        print(updated_results)

    finally:
        # close gracefully
        await graphiti.close()
        await driver.close()  # driver close if available
        print("\nConnection closed")

if __name__ == "__main__":
    asyncio.run(main())


