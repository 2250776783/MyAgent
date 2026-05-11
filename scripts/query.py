"""知识库查询脚本。

对已摄入的文档进行 RAG 检索问答。

Usage:
    uv run python scripts/query.py --question "文档内容是什么？"
    uv run python scripts/query.py --question "你好" --no-rerank --k 3
"""

import argparse
import logging
import sys

from src.llm import LLMClient
from src.rag.embed import EmbeddingClient
from src.rag.engine import RAGEngine
from src.rag.retriever import ReRanker, Retriever, VectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="查询知识库")
    parser.add_argument("--question", required=True, help="问题")
    parser.add_argument("--collection", default="documents", help="ChromaDB 集合名称")
    parser.add_argument("--k", type=int, default=5, help="向量检索候选数")
    parser.add_argument("--rerank-top-k", type=int, default=3, help="重排序保留数")
    parser.add_argument("--no-rerank", action="store_true", help="禁用 LLM 重排序")
    args = parser.parse_args()

    vector_store = VectorStore(collection_name=args.collection)
    if vector_store.count() == 0:
        logger.error(
            "集合 '%s' 为空，请先运行 scripts/ingest.py 摄入文档",
            args.collection,
        )
        sys.exit(1)

    embed_client = EmbeddingClient()
    llm = LLMClient()

    reranker = None
    if not args.no_rerank:
        reranker = ReRanker(llm_client=llm, top_k=args.rerank_top_k)

    retriever = Retriever(
        vector_store=vector_store,
        embed_client=embed_client,
        reranker=reranker,
    )
    engine = RAGEngine(retriever=retriever, llm=llm)

    print(f"问题: {args.question}")
    print("正在查询...\n")

    try:
        answer, sources = engine.query_with_sources(
            args.question,
            k=args.k,
            rerank_top_k=args.rerank_top_k,
        )
    except Exception as e:
        logger.error("查询失败: %s", e)
        sys.exit(1)

    print(f"回答: {answer}\n")

    if sources:
        print("--- 来源文档 ---")
        for i, doc in enumerate(sources, 1):
            filename = doc.metadata.get("filename", "unknown")
            preview = doc.content[:120].replace("\n", " ")
            print(f"  {i}. [{filename}] {preview}...")


if __name__ == "__main__":
    main()
