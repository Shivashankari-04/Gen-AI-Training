import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, CSVLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

VECTOR_STORE_PATH = "./chroma_db"

def get_embeddings():
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddings()
    else:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def initialize_rag(filepath: str) -> int:
    if filepath.endswith('.pdf'):
        loader = PyPDFLoader(filepath)
    elif filepath.endswith('.csv'):
        loader = CSVLoader(filepath)
    else:
        return 0

    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    
    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory=VECTOR_STORE_PATH)
    vectorstore.persist()
    return len(splits)

def query_rag(query: str, user_id: str) -> str:
    embeddings = get_embeddings()
    if not os.path.exists(VECTOR_STORE_PATH):
        return "I don't have any uploaded documents yet to answer that. Please upload a file first."
        
    vectorstore = Chroma(persist_directory=VECTOR_STORE_PATH, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    if os.getenv("OPENAI_API_KEY"):
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    else:
        from langchain.chat_models.fake import FakeListChatModel
        llm = FakeListChatModel(responses=[f"Mock response to '{query}'. (Set OPENAI_API_KEY for real RAG)"])

    prompt = ChatPromptTemplate.from_template(
        "You are an advanced enterprise AI Financial Assistant.\n"
        "Use the following pieces of retrieved context to answer the user's question.\n"
        "If you don't know the answer, just say that you don't know.\n\n"
        "Context: {context}\n"
        "Question: {question}"
    )
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain.invoke(query)
