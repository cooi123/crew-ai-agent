# from langchain_redis import RedisConfig, RedisVectorStore
# from langchain_huggingface import HuggingFaceEmbeddings
# import hashlib


# EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  

# embeddings = HuggingFaceEmbeddings(
#         model_name=EMBEDDING_MODEL, 
#         model_kwargs={"device": "cpu"}
#     )



# def get_redis_vectorstore(service_id: str, project_id: str, redis_url: str = "redis://localhost:6379/0"):
#     """
#     Get a Redis vector store instance for a specific service and project.
#     Uses a deterministic collection name based on service_id and project_id.
#     """
#     collection_name = generate_collection_name(project_id, service_id)
#     config = RedisConfig(
#         redis_url=redis_url,
#         index_name=collection_name
#     )
#     return RedisVectorStore(embeddings=embeddings, config=config)


