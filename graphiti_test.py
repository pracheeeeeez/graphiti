import asyncio
from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

falkor_username = os.environ.get('FALKORDB_USERNAME', None)
falkor_password = os.environ.get('FALKORDB_PASSWORD', None)
falkor_host = os.environ.get('FALKORDB_HOST', 'localhost')
falkor_port = os.environ.get('FALKORDB_PORT', '6379')
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY in your environment")

async def main():
    # 1) Connect to FalkorDB via Graphiti
    driver = FalkorDriver(
        host=falkor_host,
        port=falkor_port,
        username=falkor_username,
        password=falkor_password
    )
    graphiti = Graphiti(graph_driver=driver)

    try:
        query = "Who is the Data Scientist?"
        print(f">>> Running query: {query}")

        # High-level hybrid search
        results = await graphiti.search(query)
        print("\nRaw search results:")
        print(results)

        # Node-specific search with config
        print("\nNode-specific search results:")
        node_cfg = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        node_cfg.limit = 5
        node_results = await graphiti._search(query=query, config=node_cfg)
        print(node_results)

    finally:
        await graphiti.close()
        await driver.close()
        print("\nConnection closed.")

if __name__ == "__main__":
    asyncio.run(main())
