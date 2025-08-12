import asyncio
from dotenv import load_dotenv
import os
from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver

load_dotenv()

falkor_host = os.getenv("FALKORDB_HOST", "localhost")
falkor_port = int(os.getenv("FALKORDB_PORT", "6379"))
falkor_username = os.getenv("FALKORDB_USERNAME", None)
falkor_password = os.getenv("FALKORDB_PASSWORD", None)

async def main():
    driver = FalkorDriver(
        host=falkor_host,
        port=falkor_port,
        username=falkor_username,
        password=falkor_password
    )
    graphiti = Graphiti(graph_driver=driver)

    try:
        question = "hwo is Alice related to Bob?"

        print(f"=== Query: {question} ===\n")
        results = await graphiti.search(question)
        # Print search results
        print('\nSearch Results:')
        for result in results:
            print(f'UUID: {result.uuid}')
            print(f'Fact: {result.fact}')
            if hasattr(result, 'valid_at') and result.valid_at:
                print(f'Valid from: {result.valid_at}')
            if hasattr(result, 'invalid_at') and result.invalid_at:
                print(f'Valid until: {result.invalid_at}')
            print('---')

    finally:
        await graphiti.close()
        await driver.close()

if __name__ == "__main__":
    asyncio.run(main())
