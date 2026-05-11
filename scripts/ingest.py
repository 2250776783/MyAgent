"""文档摄入脚本。

将本地文档加载、切分、向量化后存入 ChromaDB 向量存储。
支持单文件和目录批量摄入。

Usage:
    uv run python scripts/ingest.py --path ./data/sample.txt
    uv run python scripts/ingest.py --path ./data --chunk-size 300
"""

import argparse
import logging
from pathlib import Path

from src.rag.embed import EmbeddingClient
from src.rag.loader import DirectoryLoader, FileLoader
from src.rag.retriever import VectorStore
from src.rag.splitter import RecursiveCharacterSplitter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="摄入文档到知识库")
    parser.add_argument("--path", required=True, help="文件或目录路径")
    parser.add_argument("--chunk-size", type=int, default=500, help="切分块大小")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="切分重叠大小")
    parser.add_argument("--collection", default="documents", help="ChromaDB 集合名称")
    parser.add_argument("--glob", default="**/*", help="文件匹配模式（目录模式时有效）")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        logger.error("路径不存在: %s", path)
        return

    logger.info("加载文档: %s", path)
    docs = (
        DirectoryLoader(path, glob_pattern=args.glob).load()
        if path.is_dir()
        else FileLoader(path).load()
    )

    if not docs:
        logger.warning("未加载到任何文档")
        return
    logger.info("加载了 %d 个文档", len(docs))

    splitter = RecursiveCharacterSplitter(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    chunks = splitter.split(docs)
    logger.info("切分为 %d 个文本块", len(chunks))

    embed_client = EmbeddingClient()
    embeddings = embed_client.embed_batch([c.content for c in chunks])
    if not embeddings:
        logger.error("向量化失败，请检查嵌入服务配置")
        return
    logger.info("生成了 %d 个向量（维度: %d）", len(embeddings), len(embeddings[0]))

    store = VectorStore(collection_name=args.collection)
    store.add(chunks, embeddings)
    logger.info(
        "已存储到集合 '%s'，共 %d 条",
        args.collection,
        store.count(),
    )


if __name__ == "__main__":
    main()
