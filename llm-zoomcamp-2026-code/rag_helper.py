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


class RAGBase:

    def __init__(
        self,
        index,
        llm_client,
        instructions: str = INSTRUCTIONS,
        course: str = "llm-zoomcamp",
        model: str = "gemini-3.5-flash-lite",
    ):
        self.index = index
        self.llm_client = llm_client
        self.instructions = instructions
        self.course = course
        self.model = model

        # Gemini receives the method reference in tools
        self.chat = self.llm_client.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.instructions,
                tools=[self.search],
            ),
        )

    def search(self, query: str, num_results: int = 5) -> list[dict]:
        """Search the FAQ database for entries matching the given query text.

        Args:
            query: The search query text to look up in the course FAQ.
            num_results: The maximum number of relevant FAQ records to return.
        """
        boost_dict = {"question": 3.0, "section": 0.5}
        filter_dict = {"course": self.course}

        return self.index.search(
            query,
            num_results=num_results,
            boost_dict=boost_dict,
            filter_dict=filter_dict,
        )

    def ask(self, user_question: str) -> str:
        """Sends user question to Gemini, triggering autonomous tool execution if needed."""
        response = self.chat.send_message(user_question)
        return response.text
