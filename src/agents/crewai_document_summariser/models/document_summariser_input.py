from pydantic import BaseModel, Field

class DocumentSummariserInputModel(BaseModel):
    """Input schema for the Document Summariser."""
    document: str = Field(
        ..., description="The document URL or the path to be summarised, This can usually be find on the document url field of the request")
    collection_name: str = Field(
        None, description="The name of the collection to be used for vector search. This can usually be find on the collection name field of the request")
    insight: str = Field(
        None, description="The insight to be extracted from the document. This can usually be find on the custom_input ")
