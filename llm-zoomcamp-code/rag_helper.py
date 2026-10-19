from google.genai import types

INSTRUCTIONS = """
You're a course teaching assistant.
You're given a question from a course student and your task is to answer it.

If you want to look up information, use the search function. 
Use as many keywords from the user question as possible when making first requests.

Make multiple searches. First perform search, analyze the results 
and then perform more searches. 

The question has to be about the course or its logistics, offtopic questions 
shouldn't be answered. If the search returns nothing, it's likely an off-topic question.
If you can't answer the question using FAQ, don't do it yourself. Only use the 
facts from the FAQ database.

At the end, ask if there are other areas that the user wants to explore.
""".strip()


def vec_to_str(vector) -> str:
    """Converts a numerical vector/array into a PostgreSQL vector string format."""
    return "[" + ",".join(str(x) for x in vector) + "]"


class RAGBase:

    def __init__(
        self,
        index=None,
        llm_client=None,
        instructions: str = INSTRUCTIONS,
        course: str = "llm-zoomcamp",
        model: str = "gemini-3.5-flash-lite",
    ):
        self.index = index
        self.llm_client = llm_client
        self.instructions = instructions
        self.course = course
        self.model = model

        # Creates chat session with Automatic Function Calling (AFC)
        self.chat = self.llm_client.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.instructions,
                tools=[self.search],
            ),
        )

    def search(self, query: str, num_results: int = 5) -> list[dict]:
        """Searches the course FAQ index for relevant records.

        Args:
            query: The query text string to look up.
            num_results: The maximum number of relevant documents to retrieve.
        """
        raise NotImplementedError("Subclasses must implement the search method.")

    def ask(self, user_question: str) -> str:
        """Sends user question to Gemini, triggering autonomous tool execution if needed."""
        response = self.chat.send_message(user_question)
        return response.text


class RAGPgVector(RAGBase):

    def __init__(self, embedder, conn, **kwargs):
        self.embedder = embedder
        self.conn = conn
        super().__init__(index=None, **kwargs)

    def search(self, query: str, num_results: int = 5) -> list[dict]:
        """Searches the PostgreSQL pgvector database for relevant FAQ entries.

        Args:
            query: The search term or student question to match against documents.
            num_results: The maximum number of matching records to return.
        """
        query_vector = self.embedder.encode(query)
        query_str = vec_to_str(query_vector)

        rows = self.conn.execute(
            """
            SELECT course, section, question, answer
            FROM documents
            WHERE course = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (self.course, query_str, num_results),
        ).fetchall()

        return [
            {"course": r[0], "section": r[1], "question": r[2], "answer": r[3]}
            for r in rows
        ]
