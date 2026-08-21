from app.ai.llm.provider import get_llm


def main():
    llm = get_llm()

    response = llm.invoke(
        "Say exactly: LLM connection successful"
    )

    print("\nGemini response:")
    print(response.content)


if __name__ == "__main__":
    main()